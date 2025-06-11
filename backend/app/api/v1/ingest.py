import logging
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session

from ...services.rag_service import RAGService, get_rag_service
from ...db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
):
    """
    Uploads a document (.txt, .md, or .pdf), processes its content, and ingests it into the knowledge base.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file name provided.")

    supported_extensions = {".txt", ".md", ".pdf"}
    if not any(file.filename.endswith(ext) for ext in supported_extensions):
        raise HTTPException(status_code=400, detail=f"Invalid file type. Supported types: {', '.join(supported_extensions)}")

    try:
        content = await file.read()
        await rag_service.ingest_document(
            db=db,
            file_name=file.filename,
            content=content
        )
        return {"message": f"Successfully ingested '{file.filename}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to ingest file: {e}")