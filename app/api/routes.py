from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.rag_service import generate_response
from app.services.ingestion import ingest_confluence
from app.core.security import get_api_key
from app.services.session_service import session_manager

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []


class IngestRequest(BaseModel):
    space_key: str
    limit: int = 10


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
        signature = request.headers.get("X-Twilio-Signature", "")

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
    message_body = form_data.get("Body")
    sender_id = form_data.get("From")

    print(f"New message from {sender_id}: {message_body}")

    # 5. Integramos la búsqueda del cliente en JSM
    # Limpiar el sender_id de Twilio (ej. "whatsapp:+5491156570822" o "+1234567")
    phone_for_search = (
        sender_id.replace("whatsapp:", "").replace("+", "") if sender_id else ""
    )
    print(f" [DEBUG WEBHOOK] Phone from Twilio: {sender_id} -> Cleaned: {phone_for_search}")

    from app.services.jira_service import jira_service

    customer_context = None
    if phone_for_search:
        try:
            search_term = phone_for_search
            # Intento de normalización: si empieza con 549 y es largo, probamos también sin el 549
            if len(search_term) > 10 and search_term.startswith("549"):
                search_term_trimmed = search_term[3:]
                print(f" [DEBUG WEBHOOK] Trying search with trimmed number: {search_term_trimmed}")
                customer_data = jira_service.get_customer_by_detail_field(
                    "Teléfono asociado", search_term_trimmed
                )
            else:
                customer_data = jira_service.get_customer_by_detail_field(
                    "Teléfono asociado", search_term
                )

            if customer_data and customer_data.get("customers"):
                customer = customer_data["customers"][0]
                customer_id = customer.get("id", customer.get("id", "Unknown"))
                customer_name = customer.get(
                    "displayName", customer.get("name", "Unknown")
                )
                customer_email = customer.get("email", "No email")
                customer_context = {
                    "id": customer_id,
                    "name": customer_name,
                    "email": customer_email,
                }
                print(f" [DEBUG WEBHOOK] Customer ENCONTRADO: {customer_context}")
            else:
                print(f" [DEBUG WEBHOOK] Customer NO encontrado en JSM para el término: {search_term}")
        except Exception as e:
            print(f" [DEBUG WEBHOOK] Error buscando al customer en JSM: {e}")

    resp = MessagingResponse()

    try:
        # if customer_context is None:
        #     resp.message(
        #         "¡Hola! 👋 Gracias por contactarte con *Sisorg*.\n\n"
        #         "Lamentablemente, no encontramos tu número registrado en nuestra base de datos. "
        #         "Por motivos de seguridad, *es necesario estar registrado para operar por este canal.*\n\n"
        #         "Por favor, contacta a soporte o envíanos tu nombre y correo para procesar tu alta."
        #     )
        # else:
        #     resp.message(
        #         f"¡Hola, {customer_name}! 👋 Bienvenido a *Sisorg*.\n\n"
        #         "Es un gusto saludarte. ¿En qué podemos ayudarte el día de hoy?"
        #     )
        # Get existing history for this sender
        history = session_manager.get_history(sender_id)

        # Call the RAG agent passing the customer context and history
        agent_response = generate_response(
            query=message_body, 
            chat_history=history,
            customer_context=customer_context
        )
        answer = agent_response["answer"]
        print(f"Respuesta del agente: {answer}")

        # Save to history
        session_manager.add_message(sender_id, "user", message_body)
        session_manager.add_message(sender_id, "assistant", answer)

        resp.message(answer)
    except Exception as e:
        print(f"Error generating response: {e}")
        resp.message("Lo siento, hubo un error procesando tu mensaje.")

    return Response(content=str(resp), media_type="application/xml")
