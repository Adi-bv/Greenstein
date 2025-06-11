from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings
from ..models.base import Base
from ..models.user import User

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create all tables in the database.
    Base.metadata.create_all(bind=engine)

    # Add dummy data for testing and demonstration
    db = SessionLocal()
    try:
        # Check if users already exist to avoid duplication
        if db.query(User).count() == 0:
            dummy_users = [
                User(
                    telegram_id=123456789,
                    interests=["python", "fastapi", "ai"],
                    interaction_summary="Discussed beginner Python topics."
                ),
                User(
                    telegram_id=987654321,
                    interests=["community management", "docker"],
                    interaction_summary="Asked about community guidelines and deployment."
                ),
                User(
                    telegram_id=112233445,
                    interests=["react", "typescript", "web development"],
                    interaction_summary="Shared resources on frontend development."
                )
            ]
            db.add_all(dummy_users)
            db.commit()
            print("Dummy users added to the database.")
    finally:
        db.close()