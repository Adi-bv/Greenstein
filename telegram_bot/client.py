import httpx
import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

async def get_chat_response(message: str, user_id: int) -> dict[str, Any]:
    """Gets a chat response from the backend's primary chat endpoint."""
    url = f"{BACKEND_URL}/api/v1/chat/"
    payload = {"message": message, "user_id": user_id}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=60.0) # Increased timeout for LLM
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        print(f"Error connecting to backend: {e}")
        return {"error": "Sorry, I'm having trouble connecting to my brain right now. Please try again later."}
    except httpx.HTTPStatusError as e:
        print(f"HTTP Status Error: {e.response.status_code} for URL {e.request.url}")
        return {"error": "Sorry, I received an unexpected response from the backend. The team has been notified."}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "An unexpected and mysterious error occurred. Please tell the admins."}
