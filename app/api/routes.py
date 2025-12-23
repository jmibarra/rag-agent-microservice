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

    resp = MessagingResponse()
    resp.message(f"Hola! [{sender_id}] tu mensaje es: {message_body}")

    return Response(content=str(resp), media_type="application/xml")

