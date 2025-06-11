import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...services.rag_service import RAGService, get_rag_service
from ...db.session import get_db
from ...core.exceptions import LLMServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest, 
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Handles incoming chat messages and returns an AI-generated response."""
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        answer = await rag_service.query(
            db=db,
            user_query=request.message,
            user_id=request.user_id
        )
        return ChatResponse(response=answer)
    except LLMServiceError as e:
        logger.error(f"LLM service error during chat: {e}")
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {e}")
    except Exception as e:
        logger.error(f"Unexpected error handling chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
