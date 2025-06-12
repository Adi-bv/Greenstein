# API Manifest

This document provides a detailed manifest of all available API endpoints for the Greenstein backend.

---

## 1. Agent Endpoint

This endpoint provides access to the Master Agent, which can perform complex, multi-step tasks using a suite of tools.

### `POST /api/v1/agent/execute`

-   **Purpose**: Accepts a user request, orchestrates the necessary tool(s) via the ReAct loop, and returns the final result. This is the primary endpoint for all agentic tasks.
-   **Tags**: `["Agents"]`

#### Request Body

```json
{
  "user_request": "string"
}
```

-   `user_request` (string, required): The user's natural language request for the agent to handle.

#### Responses

-   **`200 OK`**: The agent successfully completed the task.

    **Response Body**
    ```json
    {
      "result": "Any"
    }
    ```
    -   `result` (Any): The final result produced by the agent. The data type depends on the tool executed (e.g., a string for a summary, a JSON object for extracted action items).

-   **`400 Bad Request`**: The request was invalid or the agent failed during its execution. The response detail will contain a user-friendly error message.
-   **`422 Unprocessable Entity`**: The request body does not match the required schema (e.g., `user_request` is missing or not a string).
-   **`500 Internal Server Error`**: An unexpected error occurred on the server.

---

## 2. Chat Endpoint

This endpoint provides access to the RAG-powered chat functionality.

### `POST /api/v1/chat/`

-   **Purpose**: Handles a user's chat message, performs a hybrid (semantic + keyword) search on the knowledge base to find relevant context, and generates a personalized, context-aware response.
-   **Tags**: `["Chat"]`

#### Request Body

```json
{
  "user_id": "integer",
  "message": "string"
}
```

-   `user_id` (integer, optional): The unique identifier for the user. If provided, the response will be personalized using the user's interests and interaction history.
-   `message` (string, required): The user's chat message.

#### Responses

-   **`200 OK`**: A response was successfully generated.

    **Response Body**
    ```json
    {
      "response": "string"
    }
    ```
    -   `response` (string): The AI-generated response to the user's message.

-   **`422 Unprocessable Entity`**: The request body does not match the required schema.
-   **`500 Internal Server Error`**: An unexpected error occurred while processing the chat request.
-   **`503 Service Unavailable`**: A database error occurred during the process.

---

## 3. Ingestion Endpoint

This endpoint is used to add new documents to the RAG knowledge base.

### `POST /api/v1/ingest/`

-   **Purpose**: Ingests a file (PDF, TXT, or MD) into the RAG pipeline. The file content is extracted, split into chunks, converted into vector embeddings, and stored in the ChromaDB vector store.
-   **Tags**: `["Ingestion"]`

#### Request Body

This endpoint expects a `multipart/form-data` request containing a file upload.

-   `file` (file, required): The document to be ingested.

#### Responses

-   **`200 OK`**: The file was successfully ingested.

    **Response Body**
    ```json
    {
      "message": "string",
      "file_name": "string"
    }
    ```
    -   `message` (string): A confirmation message (e.g., "File ingested successfully.").
    -   `file_name` (string): The name of the ingested file.

-   **`400 Bad Request`**: The ingestion failed due to a service error (e.g., unsupported file type, corrupt file).
-   **`422 Unprocessable Entity`**: No file was provided in the request.
-   **`500 Internal Server Error`**: An unexpected server error occurred during ingestion.
-   **`503 Service Unavailable`**: A database error occurred during ingestion.
