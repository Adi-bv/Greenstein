# Greenstein Telegram Bot Usage Guide

This document provides a comprehensive guide on how to interact with the Greenstein Telegram Bot, your AI-powered community assistant.

---

## 1. Overview

The Greenstein bot is designed to be a central hub for our community's knowledge. It can answer questions based on an internal knowledge base, perform tasks like summarizing conversations, and ingest new documents to expand its understanding.

---

## 2. Getting Started

To begin, you can use these fundamental commands:

-   `/start`: Displays a welcome message and a brief introduction to the bot's capabilities.
-   `/help`: Provides a concise list of all available commands and how to use them.

---

## 3. Core Features

The bot's functionality is divided into three main areas: Conversational Chat, Knowledge Base Management, and Agentic Commands.

### 3.1. Conversational Chat

You can chat with the bot like you would with a person. The bot uses a powerful Retrieval-Augmented Generation (RAG) system to provide contextually relevant answers based on its knowledge base.

**How to Trigger a Response:**

-   **Private Message**: Simply send any message to the bot in a private chat.
-   **Group Mention**: In a group chat, mention the bot by its username (e.g., `@GreensteinBot`).
-   **Reply**: In a group chat, reply directly to one of the bot's messages.

### 3.2. Knowledge Base Management

The bot's intelligence is built on a knowledge base of documents. You can contribute to this knowledge base by uploading files.

**Command: `/upload`**

-   **Action**: Adds a document to the bot's knowledge base.
-   **Usage**: You **must** reply to a message containing a document with the `/upload` command.
-   **Supported File Types**: `PDF`, `TXT`, `MD` (Markdown).

**Example:**
1.  Upload a PDF file to the Telegram chat.
2.  Reply to the message containing the PDF with the text: `/upload`
3.  The bot will confirm once the file has been successfully ingested.

### 3.3. Agentic Commands

These are advanced commands that use an AI agent to perform tasks based on the recent conversation history of the chat.

**How It Works:**
When you use an agentic command, the bot sends the recent chat history (both user messages and its own replies) to a Master Agent. The agent then analyzes the conversation to fulfill your request. The quality of the output depends on the quality and length of the preceding conversation.

**Available Commands:**

-   `/summarize`: The agent reads the recent chat history and provides a concise summary of the discussion.
-   `/actions`: The agent analyzes the conversation to identify and list out any potential action items, tasks, or follow-ups that were mentioned.
-   `/highlights`: The agent extracts the most important points, decisions, or key takeaways from the conversation.

**Prompting and Format:**
-   **No special prompt is needed.** The command itself (`/summarize`, `/actions`, etc.) acts as the instruction for the agent.
-   The **context is automatically sourced** from the last 50 messages in the chat where the command is issued.
-   For best results, use these commands after a substantive discussion has taken place.

---

## 4. Quick Command Reference

| Command         | Description                                                                 | Usage Context                                     |
| --------------- | --------------------------------------------------------------------------- | ------------------------------------------------- |
| `/start`         | Displays a welcome message.                                                 | Any                                               |
| `/help`          | Shows a list of all commands.                                               | Any                                               |
| `/upload`        | Ingests a document into the knowledge base.                                 | Must be a reply to a message with a document.     |
| `/summarize`     | Provides a summary of the recent conversation.                              | After a discussion.                               |
| `/actions`       | Extracts action items from the recent conversation.                         | After a discussion.                               |
| `/highlights`    | Pulls out the key highlights from the recent conversation.                  | After a discussion.                               |

