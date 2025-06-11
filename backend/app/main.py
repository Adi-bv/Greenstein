import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
import chromadb
from sentence_transformers import SentenceTransformer

from .api.v1 import chat as chat_v1, agents as agents_v1, ingest
from .db.session import init_db
from .core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events.
    """
    logger.info("Starting up Greenstein AI Backend...")
    
    # Initialize and store expensive components in app.state
    logger.info("Initializing Sentence Transformer model...")
    app.state.rag_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    logger.info("Model initialized.")
    
    logger.info("Initializing ChromaDB client...")
    app.state.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    app.state.rag_collection = app.state.chroma_client.get_or_create_collection(name=settings.COLLECTION_NAME)
    logger.info("ChromaDB client initialized.")

    # NOTE: For production, database initialization should be handled by a migration
    # tool like Alembic. This is included for convenience in development.
    init_db()
    logger.info("Database initialized.")

    yield
    
    logger.info("Shutting down Greenstein AI Backend...")

app = FastAPI(title="Greenstein AI Backend", lifespan=lifespan)

# Include API routers with standardized tags
app.include_router(chat_v1.router, prefix="/api/v1/chat", tags=["v1", "Chat"])
app.include_router(agents_v1.router, prefix="/api/v1/agents", tags=["v1", "Agents"])
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["v1", "Ingestion"])

@app.get("/health", tags=["Monitoring"])
async def health_check():
    return {"status": "ok"}

