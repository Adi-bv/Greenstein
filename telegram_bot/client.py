import httpx
import os
from dotenv import load_dotenv
from typing import Any, Dict
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
        # Use a persistent client for connection pooling
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)

    async def close(self):
        """Closes the HTTP client session gracefully."""
        await self.client.aclose()

    async def get_chat_response(self, message: str, user_id: int) -> Dict[str, Any]:
        """Gets a chat response from the backend's RAG chat endpoint."""
        url = "/api/v1/chat/"
        payload = {"message": message, "user_id": user_id}
        
        try:
            logger.info(f"Sending chat request for user {user_id}: {message[:80]}...")
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Received chat response for user {user_id}")
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Connection error during chat for user {user_id}: {e}")
            return {"error": "Sorry, I'm having trouble connecting to my brain. Please try again later."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during chat for user {user_id}: {e.response.status_code}")
            return {"error": "Sorry, I received an unexpected response from the backend."}
        except Exception as e:
            logger.exception(f"Unexpected error during chat for user {user_id}: {e}")
            return {"error": "An unexpected and mysterious error occurred."}

    async def execute_agent_task(self, user_request: str, user_id: int) -> Dict[str, Any]:
        """Executes a task using the backend's Master Agent."""
        url = "/api/v1/agent/execute"
        payload = {"user_request": user_request}

        try:
            logger.info(f"Executing agent task for user {user_id}: {user_request}")
            response = await self.client.post(url, json=payload, timeout=120.0) # Longer timeout for agent
            response.raise_for_status()
            logger.info(f"Agent task completed for user {user_id}")
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Connection error during agent task for user {user_id}: {e}")
            return {"error": "Sorry, I can't connect to the agent right now."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during agent task for user {user_id}: {e.response.status_code}")
            return {"error": "Sorry, the agent failed to complete the task."}
        except Exception as e:
            logger.exception(f"Unexpected error during agent task for user {user_id}: {e}")
            return {"error": "An unexpected error occurred while performing the task."}

    async def ingest_file(self, file_content: bytes, filename: str, user_id: int) -> Dict[str, Any]:
        """Ingests a file into the RAG knowledge base."""
        url = "/api/v1/ingest/"
        files = {'file': (filename, file_content)}
        
        try:
            logger.info(f"Ingesting file '{filename}' for user {user_id}")
            # Use a separate client instance for file uploads to handle multipart/form-data correctly
            # with a potentially longer timeout without affecting the main client.
            async with httpx.AsyncClient(base_url=self.base_url, timeout=180.0) as file_client:
                response = await file_client.post(url, files=files)
                response.raise_for_status()
                logger.info(f"File '{filename}' ingested successfully for user {user_id}")
                return response.json()
        except httpx.RequestError as e:
            logger.error(f"Connection error during file ingestion for user {user_id}: {e}")
            return {"error": "Sorry, I couldn't upload the file. Please check the connection."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during file ingestion: {e.response.status_code}")
            if e.response.status_code == 400:
                return {"error": f"Ingestion failed: {e.response.json().get('detail', 'Unsupported file type or corrupt file')}"}
            return {"error": "Sorry, the backend had trouble processing the file."}
        except Exception as e:
            logger.exception(f"Unexpected error during file ingestion for user {user_id}: {e}")
            return {"error": "An unexpected error occurred while ingesting the file."}
