import os
import uuid
import json
from collections import deque
from dotenv import load_dotenv
from typing import Final, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction

from .client import ApiClient, logger

# Load environment variables
load_dotenv()

# --- Constants ---
TOKEN: Final = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "greenstein_bot")
ADMIN_CHAT_ID: Final = os.getenv("ADMIN_CHAT_ID")
SUPPORTED_FILE_TYPES = ['application/pdf', 'text/plain', 'text/markdown']
PROACTIVE_MESSAGE_THRESHOLD = 25 # Set to a lower number for easier testing
HISTORY_MAX_LENGTH = 100
KB_DRAFT_CONFIDENCE_THRESHOLD = 0.85

# --- Bot Application State ---
class ChatTracker:
    def __init__(self):
        self.messages = deque(maxlen=HISTORY_MAX_LENGTH)
        self.message_count_since_last_check = 0

class BotState:
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client
        self.chat_trackers: Dict[int, ChatTracker] = {}
        self.kb_drafts: Dict[str, Dict[str, str]] = {}

# --- Command Handlers (remain largely the same) ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    await update.message.reply_text(
        'Hello! I am Greenstein, your AI community assistant. I can answer questions, '
        'summarize discussions, and help manage our knowledge base. '
        'Type /help to see all my commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /help command."""
    help_text = (
        "Here's what I can do:\n\n"
        "*/chat* - Just talk to me! I'll do my best to answer your questions.\n"
        "*/summarize <text>* - I'll summarize the text you provide.\n"
        "*/extract_actions <text>* - I'll find action items in the text.\n"
        "*/highlights* - I'll give you the highlights of the recent conversation.\n"
        "*/digest* - I'll send you a private, personalized summary of recent chats.\n"
        "*File Uploads* - Send me a PDF, TXT, or MD file to add it to our knowledge base."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic handler for commands that take text arguments."""
    state: BotState = context.application.bot_data['state']
    command = update.message.text.split(' ')[0][1:]
    user_input = ' '.join(update.message.text.split(' ')[1:])
    user_id = update.message.from_user.id

    if not user_input:
        await update.message.reply_text(f"Please provide some text for the `/{command}` command.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    
    agent_request = f"{command}: {user_input}"
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    
    reply = response_data.get("result") or response_data.get("error", "Sorry, something went wrong.")
    await update.message.reply_text(reply)

async def highlights_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /highlights command."""
    state: BotState = context.application.bot_data['state']
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id

    tracker = state.chat_trackers.get(chat_id)
    if not tracker or not tracker.messages:
        await update.message.reply_text("There's not enough conversation history to generate highlights.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    conversation_history = "\n".join(f"{msg['user']}: {msg['text']}" for msg in tracker.messages)
    agent_request = f"Analyze this conversation and provide highlights: {conversation_history}"
    
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    reply = response_data.get("result") or response_data.get("error", "I couldn't generate highlights.")
    await update.message.reply_text(reply, parse_mode='Markdown')

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /digest command, sending a private message."""
    state: BotState = context.application.bot_data['state']
    user_id = update.message.from_user.id

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    await update.message.reply_text("Generating your personalized digest... I'll send it to you in a private message.")

    agent_request = "Create a personalized digest of recent community conversations for me."
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    
    reply = response_data.get("result") or response_data.get("error", "I couldn't generate your digest.")
    await context.bot.send_message(chat_id=user_id, text=reply, parse_mode='Markdown')

# --- Message & Callback Handlers ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text messages, records them, and triggers proactive checks or sends to chat."""
    state: BotState = context.application.bot_data['state']
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    text = update.message.text

    if chat_id not in state.chat_trackers:
        state.chat_trackers[chat_id] = ChatTracker()
    tracker = state.chat_trackers[chat_id]
    tracker.messages.append({'user': user_name, 'text': text})
    tracker.message_count_since_last_check += 1

    if tracker.message_count_since_last_check >= PROACTIVE_MESSAGE_THRESHOLD:
        await check_proactive_intervention(update, context)
        tracker.message_count_since_last_check = 0
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    response_data = await state.api_client.get_chat_response(text, user_id)
    reply = response_data.get("response") or response_data.get("error", "I seem to have lost my train of thought.")
    await update.message.reply_text(reply)

async def handle_file_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles file uploads for ingestion."""
    state: BotState = context.application.bot_data['state']
    user_id = update.message.from_user.id
    document = update.message.document
    if document.mime_type not in SUPPORTED_FILE_TYPES:
        await update.message.reply_text(f"Sorry, I can only process PDF, TXT, or Markdown files.")
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOADING_DOCUMENT)
    try:
        file = await document.get_file()
        file_content = await file.download_as_bytearray()
        response_data = await state.api_client.ingest_file(bytes(file_content), document.file_name, user_id)
        reply = response_data.get("message") or response_data.get("error", "File ingestion failed.")
        await update.message.reply_text(reply)
    except Exception as e:
        logger.exception(f"Error during file download/ingestion for user {user_id}: {e}")
        await update.message.reply_text("An error occurred while processing your file.")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all callbacks from inline keyboard buttons."""
    query = update.callback_query
    await query.answer()

    action, *params = query.data.split(':')
    state: BotState = context.application.bot_data['state']
    user_id = query.from_user.id

    if action == 'summarize_proactive' or action == 'find_docs_proactive':
        await handle_user_proactive_action(query, context, action)
    elif action == 'kb_approve' or action == 'kb_reject':
        await handle_admin_kb_action(query, context, action, params)
    else:
        await query.edit_message_text(text="Sorry, I don't know how to handle that action.")

# --- Proactive & Admin Logic ---
async def check_proactive_intervention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyzes conversation and decides if the bot should intervene or draft a KB article."""
    state: BotState = context.application.bot_data['state']
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    tracker = state.chat_trackers.get(chat_id)

    logger.info(f"Checking for proactive intervention in chat {chat_id}")
    conversation_history = "\n".join(f"{msg['user']}: {msg['text']}" for msg in tracker.messages)
    
    # A more advanced prompt asking for structured JSON output
    agent_request = f"""
    Analyze the following conversation. Your response MUST be a JSON object.
    1.  `proactive_suggestion`: If there is a clear recurring question, unresolved topic, or confusion, provide a short, helpful message to send to the chat. Otherwise, null.
    2.  `kb_article_draft`: If the conversation contains a valuable, resolved issue or a self-contained piece of knowledge, draft a knowledge base article. The draft should be a JSON object with `title` (string), `content` (string, markdown format), and `confidence_score` (float between 0 and 1). Otherwise, null.

    Conversation:
    {conversation_history}
    """
    
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    
    try:
        result = json.loads(response_data.get("result", "{}"))
        suggestion = result.get('proactive_suggestion')
        kb_draft = result.get('kb_article_draft')

        if kb_draft and kb_draft.get('confidence_score', 0) >= KB_DRAFT_CONFIDENCE_THRESHOLD:
            await send_draft_for_approval(kb_draft, context)
        
        if suggestion:
            keyboard = [
                [InlineKeyboardButton("Summarize Discussion", callback_data='summarize_proactive')],
                [InlineKeyboardButton("Find Related Docs", callback_data='find_docs_proactive')],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(suggestion, reply_markup=reply_markup)

    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Could not parse agent response for proactive check: {e}")
        logger.debug(f"Raw agent response: {response_data.get('result')}")

async def send_draft_for_approval(kb_draft: Dict[str, Any], context: ContextTypes.DEFAULT_TYPE):
    """Sends a drafted KB article to the admin chat for approval."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID is not set. Cannot send KB draft for approval.")
        return

    state: BotState = context.application.bot_data['state']
    draft_id = str(uuid.uuid4())
    state.kb_drafts[draft_id] = kb_draft

    title = kb_draft.get('title', 'Untitled')
    content = kb_draft.get('content', 'No content.')
    message_text = f"**New Knowledge Base Draft**\n\n**Title:** {title}\n\n**Content:**\n{content[:1000]}..."

    keyboard = [
        [InlineKeyboardButton("✅ Approve", callback_data=f'kb_approve:{draft_id}')],
        [InlineKeyboardButton("❌ Reject", callback_data=f'kb_reject:{draft_id}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    logger.info(f"Sent KB draft {draft_id} for admin approval.")

async def handle_user_proactive_action(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Handles user-facing proactive actions like 'summarize' or 'find docs'."""
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    state: BotState = context.application.bot_data['state']

    tracker = state.chat_trackers.get(chat_id)
    if not tracker or not tracker.messages:
        await query.edit_message_text(text="Sorry, I've lost the context for this conversation.")
        return

    await query.edit_message_text(text=f"Processing your request: `{action}`...")

    conversation_history = "\n".join(f"{msg['user']}: {msg['text']}" for msg in tracker.messages)
    agent_request = ""

    if action == 'summarize_proactive':
        agent_request = f"Please summarize this conversation: {conversation_history}"
    elif action == 'find_docs_proactive':
        agent_request = f"Based on this conversation, what are the key topics and can you find relevant documents from the knowledge base? Conversation: {conversation_history}"
    else:
        await query.edit_message_text(text="Sorry, I don't know how to handle that action.")
        return

    try:
        response_data = await state.api_client.execute_agent_task(agent_request, user_id)
        reply = response_data.get("result") or response_data.get("error", "I couldn't complete the request.")
        await query.edit_message_text(text=reply, parse_mode='Markdown')
    except Exception as e:
        logger.exception(f"Error handling callback action '{action}' for user {user_id}: {e}")
        await query.edit_message_text(text="An error occurred while processing your request.")

async def handle_admin_kb_action(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, action: str, params: list):
    """Handles admin actions for approving or rejecting KB drafts."""
    state: BotState = context.application.bot_data['state']
    user_id = query.from_user.id
    draft_id = params[0]

    if draft_id not in state.kb_drafts:
        await query.edit_message_text(text="This draft is no longer valid or has already been processed.")
        return

    if action == 'kb_approve':
        draft = state.kb_drafts.pop(draft_id)
        title = draft.get('title', 'Untitled Article')
        content = draft.get('content', '')
        filename = f"{title.replace(' ', '_').lower()}.md"

        try:
            await state.api_client.ingest_file(content.encode('utf-8'), filename, user_id)
            await query.edit_message_text(text=f"✅ Approved and ingested draft '{title}'.")
            logger.info(f"Admin {user_id} approved KB draft {draft_id}.")
        except Exception as e:
            logger.exception(f"Failed to ingest approved KB article {draft_id}: {e}")
            await query.edit_message_text(text="Failed to ingest the article. See logs for details.")
    
    elif action == 'kb_reject':
        state.kb_drafts.pop(draft_id)
        await query.edit_message_text(text="❌ Rejected draft.")
        logger.info(f"Admin {user_id} rejected KB draft {draft_id}.")

# --- Main Application Setup ---
async def post_init(application: Application):
    """Post-initialization hook to set up the bot state."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID environment variable not set. KB approval workflow is disabled.")
    api_client = ApiClient()
    application.bot_data['state'] = BotState(api_client)
    logger.info("Bot state initialized with ApiClient.")

async def on_shutdown(application: Application):
    """Graceful shutdown hook."""
    state: BotState = application.bot_data.get('state')
    if state and state.api_client:
        await state.api_client.close()
        logger.info("ApiClient session closed.")

def main():
    """Starts the bot."""
    logger.info("Starting bot...")

    app = Application.builder()\
        .token(TOKEN)\
        .post_init(post_init)\
        .build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler(['summarize', 'extract_actions'], agent_command))
    app.add_handler(CommandHandler('highlights', highlights_command))
    app.add_handler(CommandHandler('digest', digest_command))

    # Message & Callback Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    app.add_handler(MessageHandler(filters.Document.MimeType(SUPPORTED_FILE_TYPES), handle_file_message))
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    # Shutdown hook
    app.add_post_shutdown(on_shutdown)

    logger.info("Bot is polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
