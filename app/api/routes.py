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
