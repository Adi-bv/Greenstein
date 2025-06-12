# Greenstein Backend Architecture

## 1. Overview

The Greenstein backend is a sophisticated, AI-powered platform built with FastAPI. It is designed to be a modular, scalable, and robust system that serves as the core intelligence for the Greenstein community platform. The architecture is service-oriented, with a clear separation of concerns that makes it easy to maintain and extend.

At its heart, the backend features a powerful Retrieval-Augmented Generation (RAG) system, enhanced with hybrid search, and a true agentic system based on the ReAct (Reason, Act, Observe) framework. This allows it to not only answer questions based on a knowledge base but also perform complex, multi-step tasks using a suite of modular tools.

### Key Technologies

- **Web Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Vector Store**: ChromaDB
- **LLM Interaction**: OpenAI API with the `instructor` library for structured outputs.
- **Search**: Hybrid search combining semantic search (`sentence-transformers`) and keyword search (`rank_bm25`).
- **Data Validation**: Pydantic

## 2. Directory Structure

The backend codebase is organized into a logical and intuitive directory structure:

```
backend/
├── app/
│   ├── api/             # API endpoint definitions (routers)
│   │   └── v1/
│   ├── core/            # Core components (config, exceptions, security)
│   ├── db/              # Database setup and session management
│   ├── models/          # SQLAlchemy and Pydantic data models
│   ├── services/        # Business logic and service layer
│   └── tools/           # Modular, reusable agentic tools
├── alembic/             # Database migrations
├── tests/               # Unit and integration tests
├── .env.example         # Example environment variables
├── main.py              # FastAPI application entry point
└── requirements.txt     # Python dependencies
```

## 3. Core Components

This section details the roles and responsibilities of each major component in the `app` directory.

### `main.py`

The main entry point for the FastAPI application. Its responsibilities include:
- Initializing the FastAPI app instance.
- Configuring CORS middleware.
- Loading the Sentence Transformer model and ChromaDB collection into the application state on startup.
- Including the API routers from `app/api/v1`.

### `api/v1/`

This directory contains the API endpoints, organized by resource.

- `agents.py`: Exposes the `MasterAgent` through a single, powerful `/execute` endpoint. This is the primary interface for all complex, tool-based tasks.
- `chat.py`: Provides the RAG-powered chat functionality through the `/chat` endpoint. It handles user queries, retrieves relevant context from the RAG pipeline, and generates personalized responses.
- `ingest.py`: Manages the ingestion of documents into the knowledge base via the `/ingest` endpoint. It supports PDF, TXT, and Markdown files.

### `core/`

This directory holds the foundational components of the application.

- `config.py`: Uses Pydantic's `Settings` to manage all application configuration, loaded from environment variables.
- `exceptions.py`: Defines custom exception classes (`LLMServiceError`, `RAGServiceError`, `AgentError`) for standardized error handling.
- `security.py`: Contains the `sanitize_input` utility to mitigate prompt injection attacks by cleaning user inputs before they are processed by the LLM.

### `services/`

This is the business logic layer, where the core functionalities of the application are implemented.

- `llm_service.py`: A crucial service that acts as the primary interface to the language model. It manages a set of `PromptStrategy` enums and templates, and leverages the `instructor` library to ensure structured, validated outputs from the LLM.
- `rag_service.py`: Implements the advanced RAG pipeline. It performs **hybrid search** by combining semantic (vector) search with keyword-based (BM25) search, using Reciprocal Rank Fusion (RRF) to re-rank results for maximum relevance.
- `user_service.py`: Manages user data, including interests and interaction history. It features a "smarter memory" system that automatically summarizes long conversation histories using the LLM to keep the context relevant and concise.
- `master_agent_service.py`: The brain of the agentic system. It implements the **ReAct (Reason, Act, Observe) loop**, allowing it to solve complex, multi-step problems. It uses a "scratchpad" to maintain context throughout its reasoning process and orchestrates the tools from the `ToolRegistry`.

### `tools/`

This directory contains the modular, reusable tools that the `MasterAgent` can use to perform tasks.

- `base_tool.py`: Defines the abstract `BaseTool` class, which establishes a common interface (`name`, `description`, `execute`) for all tools.
- `summarization_tool.py`, `action_extraction_tool.py`, `categorization_tool.py`: Concrete implementations of the `BaseTool` interface, each encapsulating a specific capability.
- `tool_registry.py`: A central registry that discovers and manages all available tools. It provides the `MasterAgent` with a formatted list of tool descriptions, which is essential for the agent's planning phase.

## 4. The Agentic System (ReAct Loop)

The most advanced feature of the backend is its ReAct-style agentic system. Here’s how it works:

1.  **Request**: A user sends a complex request to the `/api/v1/agent/execute` endpoint.
2.  **Reason**: The `MasterAgent` receives the request. It uses the `REACT_AGENT_STEP` prompt strategy to ask the LLM for a `thought` and an `action` to perform, based on the user's objective and its scratchpad of previous steps.
3.  **Act**: The agent parses the LLM's response (a `ReActStep` Pydantic model) and executes the chosen tool (e.g., `summarize_text`) with the specified arguments.
4.  **Observe**: The result of the tool's execution is captured as an "observation."
5.  **Repeat**: The observation is added to the scratchpad, and the loop repeats. The agent now has more context to inform its next step.
6.  **Finish**: The loop continues until the agent determines it has the final answer and chooses the special `finish` tool, which terminates the loop and returns the result to the user.

This iterative process allows the agent to break down complex problems, gather information, and build a solution step by step, much like a human would.

## 5. Design Patterns and Principles

The backend is built upon several key design patterns and software engineering principles to ensure it is modular, maintainable, and scalable.

-   **Service-Oriented Architecture (SOA)**: The application is divided into distinct, independent services (`RAGService`, `LLMService`, `MasterAgent`, etc.), each with a specific business responsibility. This separation of concerns simplifies development, testing, and maintenance.

-   **Dependency Injection (DI)**: We leverage FastAPI's built-in support for DI using the `Depends` system. This decouples components from their dependencies, making the system more modular and easier to test. For example, services and routers receive their required dependencies (like other services or database sessions) automatically.

-   **Strategy Pattern**: The `LLMService` uses the Strategy pattern to manage different ways of interacting with the language model. The `PromptStrategy` enum defines a family of algorithms (prompt templates), and the `generate_response` method uses one of these strategies at runtime to format the request to the LLM. This makes it easy to add new LLM interaction patterns without modifying the core service.

-   **Registry Pattern**: The `ToolRegistry` acts as a centralized registry for all agentic tools. It automatically discovers all `BaseTool` subclasses, making them available to the `MasterAgent`. This pattern decouples the agent from the specific tool implementations, allowing new tools to be added with zero changes to the agent itself.

-   **Abstract Base Class (ABC)**: The `BaseTool` class is an ABC that defines a common interface (`execute`, `name`, `description`) for all tools. This ensures that any new tool created will be compatible with the `MasterAgent` and `ToolRegistry`, enforcing a consistent structure across all agentic capabilities.

## 6. Architecture Diagrams (Mermaid)

Visualizing the architecture helps in understanding the relationships and flows between different components.

### High-Level System Architecture

This diagram shows the main containers of the Greenstein platform and how they interact.

```mermaid
graph TD
    subgraph User Interfaces
        A[Telegram Bot]
        B[Web Application]
    end

    subgraph Greenstein Backend (FastAPI)
        C[API Endpoints]
        D[Master Agent]
        E[RAG Service]
        F[LLM Service]
        subgraph Tools
            ToolRegistry
        end
    end

    subgraph Data Stores
        G[SQLite DB]
        H[ChromaDB Vector Store]
    end

    subgraph External Services
        I[OpenAI API]
    end

    A --> C
    B --> C
    C --> D
    C --> E
    D -- uses --> F
    D -- uses --> ToolRegistry
    E -- uses --> F
    E -- uses --> H
    F -- calls --> I
    E -- uses --> G
    D -- uses --> G
```

### RAG Hybrid Search Pipeline

This diagram illustrates the flow of a query through the `RAGService`.

```mermaid
graph LR
    A[User Query] --> B{RAGService.query};
    B --> C[1. Semantic Search];
    B --> D[2. Keyword Search (BM25)];
    C --> E{ChromaDB};
    D --> F[In-Memory BM25 Index];
    E --> G[Semantic Results];
    F --> H[Keyword Results];
    G --> I{Reciprocal Rank Fusion (RRF)};
    H --> I;
    I --> J[Re-ranked Context];
    J --> K{LLMService};
    A --> K;
    K --> L[Generated Answer];
```

### Master Agent ReAct Loop

This diagram shows the iterative reasoning process of the `MasterAgent`.

```mermaid
graph TD
    A[User Request] --> B{MasterAgent.execute_task};
    B --> C[Initialize Scratchpad];
    C --> D{ReAct Loop (max_steps)};
    D -- 1. Reason --> E[LLMService: Generate Thought + Action];
    E --> F{Parse ReActStep};
    F -- tool_name == 'finish' --> G[Return Final Answer];
    F -- tool_name != 'finish' --> H[2. Act: Execute Tool];
    H --> I[Get Observation];
    I -- 3. Observe --> J[Update Scratchpad];
    J --> D;
    D -- max_steps reached --> K[Raise Error];
```
