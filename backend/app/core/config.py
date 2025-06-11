from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./greenstein.db"
    telegram_token: str 
    bot_username: str
    backend_url: str

    class Config:
        env_file = ".env"

settings = Settings()
