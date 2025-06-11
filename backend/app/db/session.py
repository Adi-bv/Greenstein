from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import settings
from ..models.base import Base

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
    # This is for initial setup. For migrations, Alembic is preferred.
    Base.metadata.create_all(bind=engine)
