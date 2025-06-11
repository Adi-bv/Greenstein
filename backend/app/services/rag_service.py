import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Add imports for db session and models
from ..db.session import SessionLocal
from ..db.models import User

# --- Constants ---
project_root = Path(__file__).parent.parent.parent
CHROMA_PERSIST_DIR = project_root / "chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "community_docs"

class RAGService:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        self.collection = self.chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    def _get_or_create_user(self, db, user_id: int):
        """Gets a user from the DB or creates one if they don't exist."""
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            print(f"User with telegram_id {user_id} not found. Creating new user.")
            new_user = User(telegram_id=user_id)
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user
        return user

    def query(self, user_query: str, user_id: int | None = None) -> str:
        """Performs a RAG query and returns the answer."""
        db = SessionLocal()
        try:
            if user_id:
                user = self._get_or_create_user(db, user_id)
                print(f"Query received from user: {user.id} (Telegram ID: {user.telegram_id})")

            print(f"Performing RAG query for: '{user_query}'")

            # 1. Generate query embedding
            query_embedding = self.model.encode(user_query).tolist()

            # 2. Search ChromaDB for relevant documents
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=2  # Retrieve the top 2 most relevant chunks
            )

            retrieved_docs = results.get('documents', [[]])[0]

            if not retrieved_docs:
                return "I could not find any relevant information to answer your question."

            # 3. Construct a response
            context = "\n\n---\n\n".join(retrieved_docs)
            
            response = f"Based on the community documents, here is some relevant information:\n\n{context}"

            return response
        finally:
            db.close()

# Singleton instance
rag_service = RAGService()
