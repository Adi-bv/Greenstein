from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from functools import lru_cache
from fastapi.concurrency import run_in_threadpool

from ..models.user import User

# Define fields that are allowed to be updated to prevent mass assignment vulnerabilities
ALLOWED_UPDATE_FIELDS = ["interests", "interaction_summary"]

def _db_get_user(db: Session, telegram_id: int) -> User | None:
    return db.query(User).filter(User.telegram_id == telegram_id).first()

def _db_create_user(db: Session, telegram_id: int) -> User:
    new_user = User(telegram_id=telegram_id)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except SQLAlchemyError:
        db.rollback()
        raise

def _db_append_interaction_summary(db: Session, user: User, new_interaction: str) -> User:
    current_summary = user.interaction_summary or ""
    new_summary = f"{current_summary}\n- {new_interaction}".strip()
    user.interaction_summary = new_summary
    try:
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise

def _db_update_user(db: Session, user: User, profile_data: Dict[str, Any]) -> User:
    for key, value in profile_data.items():
        if key in ALLOWED_UPDATE_FIELDS:
            setattr(user, key, value)
    try:
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise

class UserService:
    async def get_user_by_telegram_id(self, db: Session, telegram_id: int) -> User | None:
        """Asynchronously retrieve a user by their Telegram ID."""
        return await run_in_threadpool(_db_get_user, db, telegram_id)

    async def create_user(self, db: Session, telegram_id: int) -> User:
        """Asynchronously create a new user with a given Telegram ID."""
        return await run_in_threadpool(_db_create_user, db, telegram_id)

    async def get_or_create_user(self, db: Session, telegram_id: int) -> User:
        """Asynchronously retrieve a user or create them if they don't exist."""
        user = await self.get_user_by_telegram_id(db, telegram_id)
        if not user:
            user = await self.create_user(db, telegram_id)
        return user

    async def update_user_profile(self, db: Session, telegram_id: int, profile_data: Dict[str, Any]) -> User | None:
        """
        Asynchronously update a user's profile with new data.
        `profile_data` can contain 'interests' or 'interaction_summary'.
        """
        user = await self.get_user_by_telegram_id(db, telegram_id)
        if user:
            return await run_in_threadpool(_db_update_user, db, user, profile_data)
        return None

    async def update_interaction_summary(self, db: Session, telegram_id: int, new_interaction: str) -> User | None:
        """
        Appends a new interaction to the user's summary. This is key for building memory.
        """
        user = await self.get_user_by_telegram_id(db, telegram_id)
        if user:
            return await run_in_threadpool(_db_append_interaction_summary, db, user, new_interaction)
        return None

@lru_cache()
def get_user_service() -> UserService:
    return UserService()
