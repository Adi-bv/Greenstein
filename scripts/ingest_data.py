import logging
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Now that the project is an installable package, we can use direct imports
from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.db.models import DocumentMetadata

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants ---
# Use a more robust path for the data directory, assuming it's in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data"

def ingest_data():
    """
    Reads documents from the data directory, chunks them using an advanced splitter,
    generates embeddings, and upserts them into ChromaDB. This process is idempotent.
    """
    logger.info("Starting data ingestion...")

    # --- Initialize clients and services ---
    db = SessionLocal()
    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    collection = chroma_client.get_or_create_collection(name=settings.COLLECTION_NAME)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    # --- Ensure DB tables exist ---
    init_db()
    logger.info("Database initialized.")

    # --- Process files ---
    doc_files = list(DATA_PATH.glob("**/*"))
    logger.info(f"Found {len(doc_files)} files to process in {DATA_PATH}.")

    try:
        for doc_file in doc_files:
            if doc_file.is_file() and doc_file.suffix in ['.md', '.txt']:
                logger.info(f"--- Processing {doc_file.name} ---")

                # --- 1. Store metadata in SQLite (if it doesn't exist) ---
                # This part remains the same, as it's a check against the relational DB
                existing_doc = db.query(DocumentMetadata).filter(DocumentMetadata.file_name == doc_file.name).first()
                if not existing_doc:
                    new_doc_meta = DocumentMetadata(source="local", file_name=doc_file.name)
                    db.add(new_doc_meta)
                    db.commit()
                    logger.info(f"Added '{doc_file.name}' to metadata database.")

                # --- 2. Process and store content in ChromaDB using upsert ---
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Use advanced text splitter
                chunks = text_splitter.split_text(content)
                if not chunks:
                    logger.warning(f"No content chunks found in {doc_file.name}. Skipping.")
                    continue

                # Generate IDs for ChromaDB. Using upsert handles existence checks.
                ids = [f"{doc_file.name}_{i}" for i in range(len(chunks))]
                
                # Generate embeddings for all chunks
                embeddings = model.encode(chunks).tolist()

                # Use upsert to add or update chunks. This is idempotent.
                collection.upsert(
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=[{"source": doc_file.name} for _ in chunks],
                    ids=ids
                )
                logger.info(f"Upserted {len(chunks)} chunks from '{doc_file.name}' to vector store.")

    finally:
        db.close()
        logger.info("\nData ingestion complete.")

if __name__ == "__main__":
    ingest_data()
