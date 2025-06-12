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

The bot's functionality is divided into three main areas: Proactive Chat, Knowledge Base Management, and Agentic Commands.

### 3.1. Proactive Chat

The bot actively participates in group conversations. You don't always need to use a command to get its attention.

**How to Trigger a Response:**

-   **Group Mention**: In any group the bot is a member of, simply mention it by its username (e.g., `@GreensteinBot`).
-   **Reply**: Reply directly to one of the bot's messages in a group.
-   **Private Message**: Send any message to the bot in a private chat.

In all these cases, the bot will respond using its powerful Retrieval-Augmented Generation (RAG) system to provide contextually relevant answers.

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
When you use an agentic command, the bot sends the recent chat history to a Master Agent, which analyzes the conversation to fulfill your request. The quality of the output depends on the quality and length of the preceding conversation.

**Available Commands:**

-   `/report`: Provides a **detailed report** of the conversation. The agent will summarize key discussion points and is specifically instructed to retain and recite any exact information, metrics, or data mentioned.
-   `/tldr`: (Too Long; Didn't Read) Provides a **very brief, one or two-sentence summary** of the conversation. Use this for a quick overview.
-   `/actions`: Analyzes the conversation to identify and list out potential action items, tasks, or follow-ups.

**Prompting and Format:**
-   **No special prompt is needed.** The command itself acts as the instruction for the agent.
-   The **context is automatically sourced** from the last 50 messages in the chat.
-   For best results, use these commands after a substantive discussion has taken place.

### 3.4. Utility Commands

-   **`/id`**: A utility command to get the current chat's ID and your user ID. In a group, it also lists the administrators.

### 3.5. Admin Commands

These commands are restricted to bot administrators and are designed for managing the community.

**Command: `/announcement <brief>`**

-   **Action**: Generates an announcement and broadcasts it to configured groups. For security, it will **only send to groups where you (the admin) are also an administrator**.
-   **Usage**: This command must be used in a **private chat** with the bot.
-   **Example**: `/announcement The weekly meeting is rescheduled to Friday at 4 PM.`
-   **Process**:
    1.  The admin sends the command with a brief in a private message.
    2.  The AI agent expands the brief into a full announcement.
    3.  The bot verifies your admin status in each configured group and sends the message.
    4.  The admin receives a detailed confirmation report on the broadcast.

---

## 4. Quick Command Reference

| Command      | Description                                                                 | Usage Context                                     |
| ------------ | --------------------------------------------------------------------------- | ------------------------------------------------- |
| `/start`      | Displays a welcome message.                                                 | Any                                               |
| `/help`       | Shows a list of all commands.                                               | Any                                               |
| `/upload`     | Ingests a document into the knowledge base.                                 | Must be a reply to a message with a document.     |
| `/report`     | Generates a detailed report of the conversation, including metrics.         | After a discussion.                               |
| `/tldr`       | Generates a very brief summary (TL;DR) of the conversation.                 | After a discussion.                               |
| `/actions`    | Extracts action items from the recent conversation.                         | After a discussion.                               |
| `/id`         | Gets the current chat ID and your user ID.                                  | In any chat.                                      |
| `/announcement`| (Admin) Broadcasts to groups you admin.                                   | Admin only, in private chat with the bot.         |
