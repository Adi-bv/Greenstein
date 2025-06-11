import httpx
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

async def post_to_backend(endpoint: str, message: str, user_id: int | None = None) -> dict:
    """Sends a message to a backend endpoint and returns the JSON response."""
    payload = {"message": message, "user_id": user_id}
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(f"{BACKEND_URL}/{endpoint}", json=payload, timeout=30.0)
            res.raise_for_status()  # Raise an exception for bad status codes
            return res.json()
        except httpx.RequestError as exc:
            print(f"An error occurred while requesting {exc.request.url!r}.")
            return {"error": "Failed to connect to the backend."}
        except httpx.HTTPStatusError as exc:
            print(f"Error response {exc.response.status_code} while requesting {exc.request.url!r}.")
            return {"error": f"Received status {exc.response.status_code} from backend."}
