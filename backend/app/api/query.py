from fastapi import APIRouter
from pydantic import BaseModel
from ..services.rag_service import rag_service

class QueryRequest(BaseModel):
    message: str
    user_id: int | None = None

router = APIRouter()

@router.post("/")
async def handle_query(request: QueryRequest):
    """Handles a user query by passing it to the RAG service."""
    response = rag_service.query(request.message, request.user_id)
    return {"response": response}
