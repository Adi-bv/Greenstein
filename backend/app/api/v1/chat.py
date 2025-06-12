import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...services.rag_service import RAGService, get_rag_service
from ...services.user_service import UserService, get_user_service
from ...db.session import get_db
from ...core.exceptions import LLMServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    telegram_id: int | None = None

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def handle_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    user_service: UserService = Depends(get_user_service),
):
    """
    Handles incoming chat messages, provides a personalized response,
    and logs the interaction to build user memory.
    """
    if not request.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # The RAG service will automatically use user context if telegram_id is provided
        answer = await rag_service.query(
            db=db,
            user_query=request.message,
            user_id=request.telegram_id,  # Pass telegram_id to RAG service
        )

        # If a user is part of the conversation, log the interaction for future personalization
        if request.telegram_id:
            interaction_to_log = f"User: {request.message}\nAI: {answer}"
            # This runs in the background and doesn't block the response
            await user_service.update_interaction_summary(
                db, request.telegram_id, interaction_to_log
            )

        return ChatResponse(response=answer)
    except LLMServiceError as e:
        logger.error(f"LLM service error during chat: {e}")
        raise HTTPException(status_code=502, detail=f"AI service unavailable: {e}")
    except Exception as e:
        logger.error(f"Unexpected error handling chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
