import os
import sys

import requests
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

# ==========================================
# CONFIGURACIÓN
# ==========================================
CLIENT_ID = settings.JSM_CLIENT_ID
# ¡IMPORTANTE! Asegúrate de que este Secret sea el actual de la consola de Atlassian
CLIENT_SECRET = settings.JSM_CLIENT_SECRET
# Esta URL debe estar registrada en "Authorization" > "Callback URL" en la consola
CALLBACK_URL = 'http://localhost:8080/callback' 
PORT = 8080

# LISTA DE SCOPES GRANULARES (Basada en tus permisos de JSM/CSM)
SCOPES = [
    'read:customer:jira-service-management',
    'write:customer:jira-service-management',
    'read:customer.detail:jira-service-management',
    'write:customer.detail:jira-service-management',
    'read:customer.detail-field:jira-service-management',
    'write:customer.detail-field:jira-service-management',
    'read:customer:entitlement:jira-service-management',
    'write:customer:entitlement:jira-service-management',
    'read:customer.profile:jira-service-management',
    'write:customer.profile:jira-service-management',
    'read:customer-org:jira',
    'write:customer-org-info:jira',
    'offline_access'
]

# Variable global para capturar el código
authorization_code = None

class OAuthHandler(BaseHTTPRequestHandler):
    """Manejador para atrapar la redirección de Atlassian."""
    def do_GET(self):
        global authorization_code
        query_components = parse_qs(urlparse(self.path).query)
        
        if "/callback" in self.path and "code" in query_components:
            authorization_code = query_components["code"][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b"<h1>Autorizacion Exitosa</h1><p>Puedes cerrar esta ventana y volver a la consola.</p>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return # Silenciar logs del servidor

def get_authorization_url():
    """Genera la URL de autorización."""
    scope_string = " ".join(SCOPES)
    params = {
        'audience': 'api.atlassian.com',
        'client_id': CLIENT_ID,
        'scope': scope_string,
        'redirect_uri': CALLBACK_URL,
        'state': 'token_auto_flow',
        'response_type': 'code',
        'prompt': 'consent'
    }
    return 'https://auth.atlassian.com/authorize?' + urllib.parse.urlencode(params)

def exchange_code_for_token(code):
    """Realiza el intercambio del código por el access_token."""
    url = 'https://auth.atlassian.com/oauth/token'
    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': CALLBACK_URL
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"\n[!] Error 401/Unauthorized: Revisa que el CLIENT_SECRET sea correcto.")
        print(f"Status: {response.status_code}")
        print(f"Respuesta de Jira: {response.text}")
        return None

if __name__ == '__main__':
    print("=== Jira OAuth 2.0 Auto-Handler ===\n")
    
    # 1. Iniciar servidor local
    server = HTTPServer(('localhost', PORT), OAuthHandler)
    
    # 2. Abrir navegador automáticamente
    auth_url = get_authorization_url()
    print(f"Abriendo navegador para autorizar...")
    webbrowser.open(auth_url)
    
    # 3. Esperar la respuesta (solo una petición)
    print("Esperando respuesta de Atlassian en localhost:8080...")
    server.handle_request() 
    
    if authorization_code:
        print(f"\n[+] Código obtenido automáticamente.")
        print("Intercambiando por token...")
        
        token_data = exchange_code_for_token(authorization_code)
        
        if token_data:
            print("\n" + "="*60)
            print("ACCESS TOKEN (Bearer):")
            print(token_data.get('access_token'))
            print("="*60)
            
            if 'refresh_token' in token_data:
                print(f"\nREFRESH TOKEN:")
                print(token_data.get('refresh_token'))
            
            print("\nCopia el ACCESS TOKEN y úsalo en tu colección de Postman.")
    else:
        print("\n[!] No se pudo obtener el código de autorización.")