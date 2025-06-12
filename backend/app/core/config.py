from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    # Core App Settings
    DATABASE_URL: str = "sqlite:///./greenstein.db"
    OPENAI_API_KEY: str

    # LLM Settings
    LLM_MODEL: str = "gpt-3.5-turbo-1106"
    LLM_TIMEOUT: int = 30

    # Telegram Bot Settings
    TELEGRAM_TOKEN: str
    BOT_USERNAME: str
    ADMIN_CHAT_ID: int

    # RAG and VectorDB Settings
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    COLLECTION_NAME: str = "greenstein_collection"
    BACKEND_URL: str = "http://localhost:8000"
    RAG_N_RESULTS: int = 2

    @field_validator("OPENAI_API_KEY", "TELEGRAM_TOKEN", "BOT_USERNAME")
    def not_empty(cls, v):
        if not v:
            raise ValueError("Must not be empty")
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
