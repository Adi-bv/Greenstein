import logging
import io
import chromadb
import pypdf
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.concurrency import run_in_threadpool
from fastapi import Depends, Request, HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..models.document import Document
from ..core.config import settings
from ..core.exceptions import RAGServiceError, LLMServiceError
from .llm_service import LLMService, PromptStrategy, get_llm_service
from .user_service import UserService, get_user_service

logger = logging.getLogger(__name__)

def _extract_text_from_pdf(content: bytes) -> str:
    """Extracts text from a PDF file's byte content."""
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(content))
        return "".join(page.extract_text() for page in pdf_reader.pages if page.extract_text())
    except pypdf.errors.PdfReadError as e:
        logger.error(f"Failed to read PDF: {e}")
        raise RAGServiceError("Could not process PDF file. It may be corrupt or unsupported.")

def _db_check_existing(db: Session, file_name: str) -> bool:
    return db.query(Document).filter(Document.file_name == file_name).first() is not None

def _db_add_document(db: Session, doc: Document):
    try:
        db.add(doc)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

class RAGService:
    def __init__(
        self,
        llm_service: LLMService,
        user_service: UserService,
        model: SentenceTransformer,
        collection: chromadb.Collection,
    ):
        self.llm_service = llm_service
        self.user_service = user_service
        self.model = model
        self.collection = collection
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )

    async def ingest_document(self, db: Session, file_name: str, content: bytes):
        try:
            if await run_in_threadpool(_db_check_existing, db, file_name):
                logger.info(f"Document '{file_name}' already ingested. Skipping.")
                return

            text_content = ""
            if file_name.endswith(".pdf"):
                text_content = await run_in_threadpool(_extract_text_from_pdf, content)
            else: # For .txt, .md
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning(f"UTF-8 decoding failed for {file_name}, trying latin-1.")
                    text_content = content.decode("latin-1", errors="ignore")
            
            if not text_content.strip():
                raise RAGServiceError(f"No text content extracted from {file_name}.")

            chunks = self.text_splitter.split_text(text_content)
            if not chunks:
                raise RAGServiceError(f"No content chunks to ingest from {file_name}.")

            ids = [f"{file_name}_{i}" for i in range(len(chunks))]
            embeddings = await run_in_threadpool(self.model.encode, chunks)
            
            await run_in_threadpool(
                self.collection.upsert, embeddings=embeddings, documents=chunks, metadatas=[{"source": file_name}] * len(chunks), ids=ids
            )

            new_doc_meta = Document(source="local", file_name=file_name)
            await run_in_threadpool(_db_add_document, db, new_doc_meta)
            logger.info(f"Successfully ingested {len(chunks)} chunks from '{file_name}'.")

        except (RAGServiceError, LLMServiceError) as e:
            logger.error(f"Service error during ingestion: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except SQLAlchemyError as e:
            logger.error(f"Database error during ingestion: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="A database error occurred.")
        except Exception as e:
            logger.error(f"Unexpected error ingesting {file_name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="An unexpected server error occurred.")

    async def query(self, db: Session, user_query: str, user_id: int | None = None) -> str:
        logger.info(f"Performing RAG query for: '{user_query}'")
        try:
            query_embedding = await run_in_threadpool(self.model.encode, [user_query])

            results = await run_in_threadpool(
                self.collection.query, query_embeddings=query_embedding, n_results=settings.RAG_N_RESULTS
            )
            
            documents = results.get('documents', [[]])[0]
            if not documents:
                return "I could not find any relevant information to answer your question."
            document_context = "\n\n---\n\n".join(documents)

            llm_context = {"document_context": document_context, "user_query": user_query}
            strategy = PromptStrategy.GENERAL_QA

            if user_id:
                user = await self.user_service.get_or_create_user(db, user_id)
                if user:
                    logger.info(f"Personalizing query for user_id: {user.id}")
                    llm_context.update({
                        "user_interests": str(user.interests),
                        "user_interaction_summary": user.interaction_summary,
                    })
                    strategy = PromptStrategy.PERSONALIZE_RESPONSE

            return await self.llm_service.generate_response(strategy=strategy, context=llm_context)

        except (LLMServiceError, RAGServiceError) as e:
            logger.error(f"Service error during query: {e}")
            # Return a user-friendly message for known service errors
            return f"I'm sorry, but I encountered an issue: {e}"
        except Exception as e:
            logger.error(f"Unexpected error during RAG query: {e}", exc_info=True)
            return "I'm sorry, but an unexpected error occurred while processing your request."

def get_rag_service(
    request: Request,
    llm_service: LLMService = Depends(get_llm_service),
    user_service: UserService = Depends(get_user_service),
) -> RAGService:
    return RAGService(
        llm_service=llm_service,
        user_service=user_service,
        model=request.app.state.rag_model,
        collection=request.app.state.rag_collection,
    )
