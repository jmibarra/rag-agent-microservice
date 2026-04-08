from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.rag_service import generate_response
from app.services.ingestion import ingest_confluence
from app.core.security import get_api_key

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []

class IngestRequest(BaseModel):
    space_key: str
    limit: int = 50

@router.post("/chat", dependencies=[Depends(get_api_key)])
async def chat(request: ChatRequest):
    try:
        response = generate_response(request.message, request.history)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest", dependencies=[Depends(get_api_key)])
async def ingest(request: IngestRequest):
    try:
        result = ingest_confluence(request.space_key, request.limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from app.core.config import settings

@router.post("/webhook")
async def webhook(request: Request):
    # 1. Get the auth token from environment variables
    auth_token = settings.TWILIO_AUTH_TOKEN
    
    # 2. Initialize the validator
    if auth_token:
        validator = RequestValidator(auth_token)
        
        # 3. Validate the request
        url = str(request.url)
        # Validating the signature requires the full URL and parameters
        signature = request.headers.get('X-Twilio-Signature', '')
        
        # Need to parse form data
        form_data = await request.form()
        # Convert FormData to dict for validation
        form_dict = {k: v for k, v in form_data.items()}
        
        if not validator.validate(url, form_dict, signature):
            print("Validation failed!")
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        print("WARNING: TWILIO_AUTH_TOKEN not set. Skipping validation for testing.")

    form_data = await request.form()
    message_body = form_data.get('Body')
    sender_id = form_data.get('From')

    print(f"New message from {sender_id}: {message_body}")
    
    # 5. Integramos la búsqueda del cliente en JSM
    # Limpiar el sender_id de Twilio (ej. "whatsapp:+5491156570822" o "+1234567")
    phone_for_search = sender_id.replace("whatsapp:", "").replace("+", "") if sender_id else ""
    # Se añade un intento alternativo asumiendo 549 para argentina si es necesario, 
    # pero usamos el limpio por defecto.
    
    from app.services.jira_service import jira_service
    customer_context = None
    if phone_for_search:
        # Intenta buscar por el field "Teléfono de contacto"
        try:
            # Primero buscamos limpiando TODO menos los ultimos 10 digitos asumiendo codigo de area (Opcional, pero Twilio lo manda con +549)
            # Para coincidir con "1156570822", extraemos si es muy largo
            if len(phone_for_search) > 10 and phone_for_search.startswith("549"):
                phone_for_search = phone_for_search[3:] # corta el 549
            
            customer_data = jira_service.get_customer_by_detail_field("Teléfono asociado", phone_for_search)
            if customer_data and customer_data.get("customers"):
                customer = customer_data["customers"][0]
                customer_id = customer.get("id", customer.get("id", "Unknown"))
                customer_name = customer.get("displayName", customer.get("name", "Unknown"))
                customer_email = customer.get("email", "No email")
                customer_context = f"Nombre: {customer_name}, Email: {customer_email}, Customer id: {customer_id}"
                print(f"Customer identificado via JSM: {customer_context}")
            else:
                print(f"Customer no encontrado en JSM para el telefono {phone_for_search}.")
        except Exception as e:
            print(f"Error buscando al customer en JSM: {e}")

    resp = MessagingResponse()
    
    try:
        if customer_context is None:
            resp.message(
                "¡Hola! 👋 Gracias por contactarte con *Sisorg*.\n\n"
                "Lamentablemente, no encontramos tu número registrado en nuestra base de datos. "
                "Por motivos de seguridad, *es necesario estar registrado para operar por este canal.*\n\n"
                "Por favor, contacta a soporte o envíanos tu nombre y correo para procesar tu alta."
            )
        else:
            resp.message(
                f"¡Hola, {customer_name}! 👋 Bienvenido a *Sisorg*.\n\n"
                "Es un gusto saludarte. ¿En qué podemos ayudarte el día de hoy?"
            ) 
        # Call the RAG agent passing the customer context
        #agent_response = generate_response(query=message_body, customer_context=customer_context)
        #answer = agent_response["answer"]
        #resp.message(answer)
    except Exception as e:
        print(f"Error generating response: {e}")
        resp.message("Lo siento, hubo un error procesando tu mensaje.")

    return Response(content=str(resp), media_type="application/xml")

