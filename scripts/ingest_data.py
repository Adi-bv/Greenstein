import os
import sys
import chromadb
from pathlib import Path

# Add project root to path to allow importing from backend
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.app.db.session import SessionLocal, init_db
from backend.app.db.models import DocumentMetadata
from sentence_transformers import SentenceTransformer

# --- Constants ---
DATA_PATH = project_root / "data"
CHROMA_PERSIST_DIR = project_root / "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "community_docs"

def ingest_data():
    """Reads documents, generates embeddings, and stores them."""
    print("Starting data ingestion...")

    # --- Initialize clients ---
    db = SessionLocal()
    model = SentenceTransformer(EMBEDDING_MODEL)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    # --- Ensure DB tables exist ---
    init_db()
    print("Database initialized.")

    # --- Process files ---
    doc_files = list(DATA_PATH.glob("**/*"))
    print(f"Found {len(doc_files)} files to process in {DATA_PATH}.")

    for doc_file in doc_files:
        if doc_file.is_file() and doc_file.suffix in ['.md', '.txt']:
            print(f"--- Processing {doc_file.name} ---")

            # --- 1. Store metadata in SQLite (if it doesn't exist) ---
            existing_doc = db.query(DocumentMetadata).filter(DocumentMetadata.file_name == doc_file.name).first()
            if existing_doc:
                print(f"'{doc_file.name}' already in metadata DB. Skipping metadata entry.")
            else:
                new_doc_meta = DocumentMetadata(source="local", file_name=doc_file.name)
                db.add(new_doc_meta)
                db.commit()
                print(f"Added '{doc_file.name}' to metadata database.")

            # --- 2. Process and store content in ChromaDB ---
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple chunking by paragraph
            chunks = content.split('\n\n')
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

            if not chunks:
                print(f"No content chunks found in {doc_file.name}. Skipping embedding.")
                continue

            # Generate IDs for ChromaDB to check for existence
            ids = [f"{doc_file.name}_{i}" for i in range(len(chunks))]
            
            # Check which chunks are already in ChromaDB
            existing_ids = collection.get(ids=ids)['ids']
            new_chunks = [chunk for i, chunk in enumerate(chunks) if ids[i] not in existing_ids]
            new_ids = [id for id in ids if id not in existing_ids]

            if not new_chunks:
                print(f"All chunks from '{doc_file.name}' are already in the vector store. Skipping.")
                continue

            # Generate embeddings only for new chunks
            print(f"Found {len(new_chunks)} new chunks to add.")
            embeddings = model.encode(new_chunks).tolist()

            # Add to ChromaDB
            collection.add(
                embeddings=embeddings,
                documents=new_chunks,
                metadatas=[{"source": doc_file.name} for _ in new_chunks],
                ids=new_ids
            )
            print(f"Added {len(new_chunks)} chunks from '{doc_file.name}' to vector store.")

    db.close()
    print("\nData ingestion complete.")

if __name__ == "__main__":
    ingest_data()
