import shelve
from collections import deque

HISTORY_MAX_LENGTH = 50
DB_PATH = "bot_chat_history.db"

def add_message_to_history(chat_id: int, user: str, text: str):
    """Adds a message to a chat's history in a persistent shelve database."""
    with shelve.open(DB_PATH) as db:
        chat_id_str = str(chat_id)
        # Get existing history or create a new one
        history = db.get(chat_id_str, deque(maxlen=HISTORY_MAX_LENGTH))

        # Ensure the loaded object is a deque
        if not isinstance(history, deque):
            history = deque(history, maxlen=HISTORY_MAX_LENGTH)

        history.append({"user": user, "text": text})
        db[chat_id_str] = history  # Re-assign to save changes

def get_conversation_history(chat_id: int) -> str:
    """Retrieves and formats the conversation history for a given chat."""
    with shelve.open(DB_PATH) as db:
        chat_id_str = str(chat_id)
        history = db.get(chat_id_str)
        if not history:
            return ""
        return "\n".join(f"{msg['user']}: {msg['text']}" for msg in history)
