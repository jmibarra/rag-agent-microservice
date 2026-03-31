import json
import os
import requests
import time
from app.core.config import settings

class JsmOAuthManager:
    def __init__(self):
        self.client_id = settings.JSM_CLIENT_ID
        self.client_secret = settings.JSM_CLIENT_SECRET
        self.initial_refresh_token = settings.JSM_INITIAL_REFRESH_TOKEN
        self.token_file = settings.JSM_TOKEN_FILE
        self.token_data = None

        # Asegurar que el directorio data/ exista
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        self._load_tokens()

    def _load_tokens(self):
        """Intenta cargar los tokens dinámicos desde el archivo."""
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, "r") as f:
                    self.token_data = json.load(f)
            except Exception as e:
                print(f"Error cargando archivo de tokens: {e}")
                self.token_data = None
        
        # Si no hay tokens dinámicos guardados, usa el refresh token inicial del .env (si existe)
        if not self.token_data and self.initial_refresh_token:
            self.token_data = {
                "refresh_token": self.initial_refresh_token,
                "access_token": None,
                "expires_at": 0
            }

    def _save_tokens(self, data):
        """Guarda la respuesta de OAuth en disco para persistir la rotación."""
        expires_at = time.time() + data.get("expires_in", 3600) - 60  # expiración adelantada por 1 min
        
        # Atlassian puede o no devolver un nuevo refresh_token dependiendo de las policies
        # pero usualmente sí lo rota.
        new_refresh = data.get("refresh_token")
        
        self.token_data = {
            "access_token": data.get("access_token"),
            "refresh_token": new_refresh if new_refresh else self.token_data.get("refresh_token"),
            "expires_at": expires_at
        }
        
        try:
            with open(self.token_file, "w") as f:
                json.dump(self.token_data, f, indent=4)
        except Exception as e:
            print(f"Error guardando los tokens dinámicos: {e}")

    def _refresh_token(self):
        """Llama a la API de auth para conseguir un nuevo access_token usando el refresh_token."""
        if not self.token_data or not self.token_data.get("refresh_token"):
            print("No hay refresh token disponible. Asegúrate de configurar JSM_INITIAL_REFRESH_TOKEN en el .env.")
            return False

        if not self.client_id or not self.client_secret:
            print("Falta configurar JSM_CLIENT_ID o JSM_CLIENT_SECRET en el .env.")
            return False

        url = "https://auth.atlassian.com/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.token_data["refresh_token"]
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            self._save_tokens(data)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error al refrescar el token de JSM: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(e.response.text)
            return False

    def get_valid_token(self) -> str | None:
        """Devuelve un access token válido. Lo renueva si es necesario."""
        if not self.token_data:
            return None

        # Si no tenemos access_token o si ya expiró
        if not self.token_data.get("access_token") or time.time() > self.token_data.get("expires_at", 0):
            success = self._refresh_token()
            if not success:
                return None
                
        return self.token_data.get("access_token")

# Instancia global ("singleton") del manager
jsm_auth_manager = JsmOAuthManager()
