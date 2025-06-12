import httpx
import os
from dotenv import load_dotenv
from typing import Any, Dict, List
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logger for the bot
logger.add("bot.log", rotation="10 MB", level="INFO")

class ApiClient:
    """
    An asynchronous client for interacting with the Greenstein backend API.
    """
    def __init__(self, base_url: str = None):
        """
        Initializes the API client.

        Args:
            base_url: The base URL of the backend API. If not provided,
                      it's read from the BACKEND_URL environment variable.
        """
        self.base_url = base_url or os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
        logger.info(f"ApiClient initialized for base_url: {self.base_url}")
        # Use a persistent client for connection pooling
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def close(self):
        """Closes the HTTP client session gracefully."""
        logger.info("Closing ApiClient HTTP session.")
        await self.client.aclose()

    async def _handle_error(self, e: httpx.HTTPStatusError) -> Dict[str, Any]:
        """Parses an HTTPStatusError for a detailed error message."""
        logger.error(f"HTTP error from {e.request.url}: Status {e.response.status_code}")
        try:
            detail = e.response.json().get("detail", "An unknown backend error occurred.")
            # Handle Pydantic validation errors, which are often lists of dicts
            if isinstance(detail, list):
                error_msg = " ".join(d.get('msg', '') for d in detail)
                detail = f"Invalid request: {error_msg}"
            return {"error": f"Backend Error: {detail}"}
        except Exception:
            return {"error": f"Sorry, an unexpected error occurred (HTTP {e.response.status_code})."}

    async def _handle_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """A generic helper to make requests to the backend."""
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return await self._handle_error(e)
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            return {"error": "Could not connect to the backend service."}
        except Exception as e:
            logger.critical(f"An unexpected error occurred in the API client: {e}", exc_info=True)
            return {"error": "An unexpected internal error occurred."}

    async def get_chat_response(self, message: str, user_id: int) -> Dict[str, Any]:
        """Gets a chat response from the backend's RAG chat endpoint."""
        url = "/api/v1/chat/"
        payload = {"message": message[:1024], "user_id": user_id}  # Truncate for safety
        logger.info(f"Sending chat request for user {user_id} (message: '{message[:80]}...')")
        return await self._handle_request("POST", url, json=payload)

    async def execute_agent_task(self, user_request: str) -> Dict[str, Any]:
        """Executes a task using the backend's Master Agent."""
        url = "/api/v1/agent/execute"
        payload = {"user_request": user_request[:4096]}  # Truncate for safety
        logger.info(f"Executing agent task: {user_request[:80]}...")
        # Use a longer timeout for agent tasks, as they can be long-running.
        return await self._handle_request("POST", url, json=payload, timeout=120.0)

    async def ingest_file(self, file_content: bytes, filename: str, user_id: int) -> Dict[str, Any]:
        """Ingests a file into the RAG knowledge base."""
        url = "/api/v1/ingest/"
        files = {'file': (filename, file_content)}  # Let httpx set the MIME type
        logger.info(f"Ingesting file '{filename}' for user {user_id}")
        # Use a longer timeout for file uploads.
        return await self._handle_request("POST", url, files=files, timeout=180.0)
