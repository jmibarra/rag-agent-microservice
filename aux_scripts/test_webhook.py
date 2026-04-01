import os
import sys
import requests
from twilio.request_validator import RequestValidator

# Cargar configuraciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Hardcodeamos el token original que está esperando Twilio/FastAPI
auth_token = "65f14f6e0401e4b238e9e9f3ac45bf86"
validator = RequestValidator(auth_token)

url = "http://localhost:8000/api/v1/webhook"
params = {
    "Body": "Hola agente",
    "From": "whatsapp:+5491156570822" # Teléfono que coincide con tu usuario
}

# Twilio firma matemáticamente los parámetros y la URL exacta usando el Auth Token
signature = validator.compute_signature(url, params)
print(f"Firma Twilio Calculada: {signature}")

# Hacemos el POST simulando ser los servidores de Twilio
headers = {
    "X-Twilio-Signature": signature,
    "Content-Type": "application/x-www-form-urlencoded"
}

print(f"\nDisparando request a {url}...")
response = requests.post(url, data=params, headers=headers)

print(f"Status Code: {response.status_code}")
print("Response XML:")
print(response.text)
