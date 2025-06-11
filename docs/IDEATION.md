## Project Ideation: "Greenstein" - AI Community Core & Hub

**1. Project Vision:**

To create "Greenstein," starting with a powerful AI-driven backend and RAG system that acts as the intelligent core for community information management. This core will then be exposed through dynamic bots on platforms like Telegram (and conceptually Discord), providing seamless agentic assistance directly within existing chat environments. Finally, a comprehensive web application will offer users a dedicated dashboard, personalized chat interaction with the AI steward leveraging full community context, and advanced agentic capabilities. The entire system will be designed with Salesforce ecosystem principles at its heart.

**2. Core Problem Statement (Recap & Phased Focus):**

Community communication is fragmented and overwhelming. Greenstein addresses this by first building an intelligent backend "brain" to understand and manage community knowledge. This intelligence is then made accessible via familiar chat platforms, and ultimately, through a rich native web experience, transforming community interaction from reactive to proactively assisted and informed.

**3. Target Users:**

- **Phase 1 (Backend Focus):** Primarily developers/admins (simulated) interacting with APIs.
- **Phase 2 (Bot Focus):** Green Meadows Community Members on Telegram/Discord.
- **Phase 3 (Web App Focus):** Green Meadows Community Members and Community Managers using the dedicated platform.

**4. Key Goals for the Project:**

- **Robust AI Core:** Develop a strong backend with advanced NLU, RAG, and foundational agentic logic.
- **Dynamic Bot Integrations:** Showcase seamless AI steward functionality within external chat platforms, personalized by user context.
- **Comprehensive Web Hub:** Create a rich, interactive web application for direct user engagement with the AI steward and community data.
- **Scalable & Modular Design:** Build components that can be independently developed and integrated.
- **Salesforce Ecosystem Alignment:** Ensure all phases and components have clear conceptual mappings to Salesforce.

**5. High-Level PoC Architecture (Phased View):**

**Phase 1: Backend AI Core & Business Logic**

- **A1. Backend Orchestration & Agentic Logic Layer:**
    - **PoC Implementation:** Python (Flask/FastAPI) or Node.js (Express).
    - **Responsibilities:** API endpoints for all core AI functions (categorization, Q&A, summarization, recommendations, basic agentic task primitives). Internal logic for processing, RAG, and interfacing with LLMs. Manages (mocked) user context/data for personalization.
    - **Salesforce Mapping:** Salesforce Flow, Apex, Platform Events, Einstein services.
- **B1. Generative AI Core:**
    - **PoC Implementation:** Third-party LLM API (OpenAI GPT-3.5/4, Claude). Focus on building robust prompt libraries for diverse tasks.
    - **Salesforce Mapping:** Salesforce Einstein GPT.
- **C1. Community Knowledge & Data Layer (Mocked & Internal):**
    - **PoC Implementation:**
        - **Internal PoC Database:** (e.g., SQLite, PostgreSQL) for user profiles (mocked interests, roles), community documents metadata, vectorized embeddings.
        - **Vector Database Engine:** (e.g., integrated ChromaDB, FAISS) for RAG.
        - **Mock APIs for External Data (if needed):** e.g., for event schedules, service provider lists.
    - **Salesforce Mapping:** Data Cloud, Salesforce Files/Knowledge/CMS, Custom Objects, Einstein Search Indexing.

**Phase 2: External Bot Integrations (Telegram, then Discord - Conceptual)**

- **D2. Telegram Bot Module:**
    - **PoC Implementation:** Python script using `python-telegram-bot` (or similar).
    - **Responsibilities:** Authenticates with Telegram API. Listens to messages in configured groups. Forwards user queries/messages to the Backend AI Core APIs. Receives processed responses/actions from backend. Formats and sends messages back to Telegram. Manages Telegram user ID mapping to internal user profiles for context.
    - **Salesforce Mapping:** MuleSoft / Custom Apex Callouts & REST Services.
- **E2. Discord Bot Module (Conceptual for Hackathon, similar architecture):**
    - **PoC Implementation (if time permits, likely out of scope for 1-day):** Similar to Telegram bot, using Discord.js or other libraries.
    - **Salesforce Mapping:** Similar integration patterns as Telegram.

**Phase 3: Native Web Application & Dashboard**

- **F3. Frontend - Web Application & Dashboard:**
    - **PoC Implementation:** Web application (React, Vue, Svelte).
    - **Responsibilities:** User authentication (mocked). Dashboard view for community highlights, AI-generated summaries, event calendars. Personalized chat interface for direct interaction with the AI steward (leveraging full user context from backend). Interface for community managers (reviewing AI actions, managing content).
    - **Salesforce Mapping:** Salesforce Experience Cloud site with custom LWCs, CRM Analytics for dashboards.
- **G3. Backend API Gateway & Web Sockets (for Web App):**
    - **PoC Implementation:** Extend Phase 1 Backend or use a dedicated API Gateway. Implement WebSockets ([Socket.IO](http://socket.io/)) for real-time chat in the web app.
    - **Salesforce Mapping:** Experience Cloud backend logic, Streaming API / Platform Events for real-time.

**6. Feature List & Prioritization (Phased):**

**Phase 1: Building the Core (Backend & AI Foundation)**

| Feature | Description | PoC Tech Stack & Implementation Notes (Backend Focus) | Salesforce Mapping | Priority |
| --- | --- | --- | --- | --- |
| **1.1. Core API Endpoints** | Expose APIs for: message categorization, RAG-based Q&A, text summarization, basic content recommendation. | Python (Flask/FastAPI) or Node.js. RESTful API design. | Apex REST Services, Invocable Actions for Flow | High |
| **1.2. LLM Integration & Prompt Library** | Integrate with an LLM. Develop a set of robust prompts for the core API functions. | Direct API calls to OpenAI/Claude. Store prompts in config or simple DB. | Einstein GPT (prompts managed via Prompt Builder or called from Apex/Flow) | High |
| **1.3. RAG Pipeline (Docs & Basic History)** | Implement RAG for Q&A using (mocked) community documents and a small, static sample of (mocked) conversation history. | Sentence Transformers for embeddings, local Vector DB (ChromaDB/FAISS). Backend logic to orchestrate retrieval and generation. | Salesforce Knowledge, Custom Objects for chat history, Einstein Search indexing, Einstein GPT | High |
| **1.4. User Context Management (Mocked)** | Backend can associate requests with a (mocked) user ID and retrieve basic preferences/roles to slightly tailor AI responses (e.g., tone). | Simple dictionary/DB lookup for user profiles. Pass context to LLM prompts. | Data Cloud / User Object fields | High |
| **1.5. Basic Agentic Primitives (Internal)** | Internal functions for potential agentic flows (e.g., "identify_key_entities", "draft_reply_template", "log_interaction_summary"). | Python/Node.js functions within the backend. These are building blocks, not yet fully autonomous agents. | Reusable Apex methods, Invocable Flow Actions | Medium |

**Phase 2: External Integration Focus (Telegram Bot First)**

| Feature | Description | PoC Tech Stack & Implementation Notes (Bot Focus) | Salesforce Mapping | Priority |
| --- | --- | --- | --- | --- |
| **2.1. Telegram Bot: Basic Connectivity & Message Forwarding** | Bot connects to Telegram, listens to a group, and forwards user messages to the Phase 1 Backend API. | `python-telegram-bot`. Basic message handlers. API calls to backend. | MuleSoft / Custom Apex Inbound REST Service | High |
| **2.2. Telegram Bot: Displaying AI Responses** | Bot receives processed responses (Q&A answers, summaries) from the backend and posts them to the Telegram group. | `python-telegram-bot` to send messages. Formatting for Telegram. | MuleSoft / Custom Apex Outbound Call to Telegram API | High |
| **2.3. Telegram Bot: Contextual Q&A** | Telegram users can ask questions; bot uses their Telegram ID (mapped to internal profile) for context when calling backend Q&A. | Bot extracts user ID, passes it to backend API. Backend uses this for contextual RAG. | As above, with user context passed | High |
| **2.4. Telegram Bot: On-Demand Summaries** | User can command bot (e.g., `/summarize_last_hour`) to get a summary of recent (mocked or actual if ingesting) chat via backend. | Bot recognizes command, calls backend summarization API with parameters. | As above, triggering a summarization Flow/Apex method | Medium |
| **2.5. Telegram Bot: Basic Agentic Interaction (e.g., Info Retrieval Task)** | User asks bot to find specific info (e.g., "/find_event_rules"). Bot uses backend agentic primitive to retrieve & present. | Bot command triggers specific backend agentic function (which might involve RAG or a specific data lookup). | As above, invoking a more complex backend process. | Medium |
| **2.6. (Stretch) Discord Bot: Basic Connectivity (if time)** | Similar to 2.1 & 2.2 for Discord. | `discord.js` or similar. (Lower priority due to time). | Similar to Telegram. | Low |

**Phase 3: Custom Web Application & Dashboard**

| Feature | Description | PoC Tech Stack & Implementation Notes (Web App Focus) | Salesforce Mapping | Priority |
| --- | --- | --- | --- | --- |
| **3.1. Web App: User Auth & Basic Dashboard** | Mock user login. Dashboard displays community announcements (AI-generated or admin-posted), upcoming events (mocked). | React/Vue. Simple state management. Calls to backend APIs for dashboard data. | Experience Cloud (Login, Home Page with LWC components showing Knowledge, Events) | High |
| **3.2. Web App: Personalized AI Chat Interface** | Users can chat directly with the AI steward. Conversation history is maintained. AI uses full user context and ongoing chat context. | React/Vue chat component. WebSockets ([Socket.IO](http://socket.io/)) for real-time. Calls backend AI APIs. | Experience Cloud with Embedded Chat (LWC), Einstein Bot (with deep Einstein GPT integration) | High |
| **3.3. Web App: Access to Knowledge & Summaries** | Users can browse AI-generated topic summaries, search community documents (via AI), and see highlighted important messages. | UI components to display data fetched from backend APIs (summaries, RAG search results). | Experience Cloud (Knowledge Search, Custom LWC displays) | Medium |
| **3.4. Web App: Agentic Task Initiation** | Users can explicitly ask the AI chat steward to perform tasks (e.g., "Help me draft an event proposal," "Summarize the discussion on X for me"). | Chat interface sends commands to backend, triggering more complex agentic flows. AI might ask clarifying questions within the chat. | Einstein Bot with Dialogs that trigger Flows/Apex actions, using Einstein GPT for generation/understanding. | Medium |
| **3.5. Web App: Community Manager View (Basic)** | Simple interface for admins to see AI-flagged content, review AI-drafted announcements, or trigger community-wide AI actions (e.g., "Summarize day"). | Separate route/components in the web app for admin functions. Calls to specific backend admin APIs. | Custom Salesforce App Page with LWCs for Admins / Service Cloud Console (if managing community issues) | Medium |

**7. State-of-the-Art Technologies & Integration:**

- **Backend Focus:** Python (Flask/FastAPI) / Node.js (Express), LLM APIs (OpenAI/Claude), Vector DBs (ChromaDB/FAISS), Sentence Transformers for RAG.
- **Bot Integration Focus:** `python-telegram-bot` (or `discord.js`). Secure API communication with the backend.
- **Web App Focus:** React/Vue/Svelte, WebSockets ([Socket.IO](http://socket.io/)).

**8. Inspiration from Existing Solutions & Market Trends:**

- **Modular AI Services:** Services like AWS Lambda/Google Cloud Functions for microservice-based AI logic (relevant to backend design).
- **Enterprise Bots:** Slack/Teams bots that integrate deeply with backend systems.
- **Customer Service Platforms (Zendesk, Intercom):** How they centralize data and then expose it via multiple channels.
- **Salesforce Platform:** As a comprehensive example of a core platform with extensible UIs and integration capabilities.