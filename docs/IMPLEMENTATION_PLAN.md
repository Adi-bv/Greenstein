# Greenstein - Phased Implementation Plan

This document outlines the detailed, phased implementation plan for the Greenstein project. The goal is to refactor the existing code and build a modular, scalable, and well-organized system based on the project's ideation and architecture documents.

---

## **Phase 0: Project Setup & Refactoring**

This initial phase focuses on establishing a clean, organized, and scalable project structure. We will refactor the existing code into this new structure.

**Goals:**
-   Create a modular directory structure.
-   Separate concerns for the backend, telegram bot, and future web application.
-   Set up dependency management.
-   Refactor existing code into the new structure.

**Tasks:**

1.  **Directory Structure:**
    -   `backend/`: Main FastAPI application.
        -   `app/`: Core application logic.
            -   `api/`: API endpoints/routers.
            -   `core/`: Configuration, startup events, etc.
            -   `services/`: Business logic (RAG, user context, etc.).
            -   `models/`: Pydantic models for API requests/responses.
            -   `db/`: Database session management and models (SQLAlchemy).
            -   `rag/`: RAG pipeline components (data loaders, vector store, etc.).
        -   `main.py`: FastAPI application entry point.
    -   `telegram_bot/`: Telegram bot logic.
        -   `bot.py`: Main bot logic, command handlers.
        -   `client.py`: A client to communicate with the backend API.
    -   `docs/`: Project documentation.
    -   `.env`: Environment variables.
    -   `requirements.txt`: Python dependencies.

2.  **Refactor `telegram_bot/main.py`:**
    -   Move the core bot logic into `telegram_bot/bot.py`.
    -   Extract the `httpx` calls into a dedicated `telegram_bot/client.py`. This client will be responsible for all communication with the backend.
    -   The `handel_response` function will be split. The keyword checking will remain in the bot, but the actual processing will be delegated to the backend via the new client.

3.  **Refactor Backend Code:**
    -   Move the backend-related logic from `telegram_bot/main.py` into the new `backend/` structure.
    -   Create initial FastAPI endpoints in `backend/app/api/` for `/query` and `/filter`.
    -   Set up the basic FastAPI application in `backend/main.py`.

---

## **Phase 1: Core AI Backend Development**

This phase focuses on building the "brain" of the system as outlined in the architecture.

**Goals:**
-   Implement a robust RAG pipeline.
-   Develop core API endpoints for AI functionalities.
-   Set up database models for user context and document metadata.

**Tasks:**

1.  **Database Setup (SQLite & SQLAlchemy):**
    -   Define SQLAlchemy models in `backend/app/db/models.py` for `User` and `DocumentMetadata`.
    -   Implement database session management in `backend/app/db/session.py`.

2.  **RAG Pipeline (ChromaDB):**
    -   Implement a `DataIngestionService` in `scripts/ingest_data.py`. This script will:
        -   Load documents from a local `data/` directory.
        -   Split documents into chunks.
        -   Generate embeddings using a sentence-transformer model.
        -   Store embeddings and metadata in ChromaDB.
        -   Store document metadata in the SQLite database.
    -   Implement a `RAGService` in `backend/app/services/rag_service.py` that can:
        -   Take a user query.
        -   Generate a query embedding.
        -   Perform a similarity search in ChromaDB to retrieve relevant context.
        -   Construct a prompt for the LLM.
        -   Call the LLM and return the response.

3.  **API Endpoint Development:**
    -   Enhance the `/query` endpoint in `backend/app/api/query.py` to use the `RAGService`.
    -   Create a `/summarize` endpoint.
    -   Implement basic user context management, passing user info to the RAG service.

---

## **Phase 2: Telegram Bot Integration**

Connect the Telegram bot to the fully developed backend.

**Goals:**
-   Make the bot a clean interface to the backend services.
-   Enable contextual conversations.

**Tasks:**

1.  **Update `telegram_bot/client.py`:**
    -   Add methods to call the new backend endpoints (`/query`, `/summarize`).
2.  **Enhance `telegram_bot/bot.py`:**
    -   Refactor command handlers (`start_command`, etc.) to be more robust.
    -   Update `handle_message` to use the client to call the appropriate backend service based on the message content.
    -   Pass the Telegram User ID to the backend with every request to enable user-specific context.

---

## **Phase 3: Web Application (Future Scope)**

This phase is for future development and involves building the user-facing web dashboard.

**Goals:**
-   Provide a rich user interface for interacting with the AI.
-   Offer administrative and community management features.

**Tasks (High-Level):**

1.  **Frontend Development (React/Vue):**
    -   Set up the frontend project.
    -   Implement user authentication (mocked).
    -   Build a chat interface using WebSockets.
2.  **Backend Enhancements for Web App:**
    -   Add WebSocket support to the FastAPI backend.
    -   Create new API endpoints required for the dashboard (e.g., fetching conversation history, user profiles).

This plan provides a clear roadmap. We will start with Phase 0 to establish a solid foundation before moving on to core feature development.