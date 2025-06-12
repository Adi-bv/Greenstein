import os
import uuid
import json
from collections import deque
from dotenv import load_dotenv
from typing import Final, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram.constants import ChatAction, ChatType

from .client import ApiClient, logger

# Load environment variables
load_dotenv()

# --- Constants ---
TOKEN: Final = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "greenstein_bot")
ADMIN_CHAT_ID: Final = os.getenv("ADMIN_CHAT_ID")
SUPPORTED_FILE_TYPES = ['application/pdf', 'text/plain', 'text/markdown']
PROACTIVE_MESSAGE_THRESHOLD = 25
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

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /start command from user {update.effective_user.id} in chat {update.effective_chat.id}")
    await update.message.reply_text(
        'Hello! I am Greenstein, your AI community assistant. I can answer questions, '
        'summarize discussions, and help manage our knowledge base. '
        'Type /help to see all my commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /help command from user {update.effective_user.id} in chat {update.effective_chat.id}")
    help_text = (
        "Here's what I can do:\n\n"
        f"*Mention @{BOT_USERNAME}* or reply to my messages to chat with me in a group.\n\n"
        "*/summarize* - I'll summarize the recent conversation.\n"
        "*/extract_actions* - I'll find action items in the recent conversation.\n"
        "*/highlights* - I'll give you the highlights of the recent conversation.\n"
        "*/digest* - I'll send you a private, personalized summary of recent chats.\n"
        "*/upload* - Attach a file (document or image) and use this command as the caption to add it to the knowledge base."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def contextual_agent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received contextual agent command from user {update.effective_user.id} in chat {update.effective_chat.id}")
    """Handler for agent commands that operate on conversation history."""
    state: BotState = context.application.bot_data['state']
    command = update.message.text.split(' ')[0][1:]
    logger.debug(f"Processing command: {command}")
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id

    tracker = state.chat_trackers.get(chat_id)
    if not tracker or not tracker.messages:
        await update.message.reply_text("There's not enough conversation history for me to work with.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    conversation_history = "\n".join(f"{msg['user']}: {msg['text']}" for msg in tracker.messages)
    agent_request = f"Based on the following conversation, perform the action '{command}':\n\n{conversation_history}"
    
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    reply = response_data.get("result") or response_data.get("error", f"I couldn't perform the `/{command}` action.")
    logger.info(f"Sending reply for command '{command}' to chat {chat_id}")
    await update.message.reply_text(reply, parse_mode='Markdown')

async def digest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /digest command from user {update.effective_user.id}")
    state: BotState = context.application.bot_data['state']
    user_id = update.message.from_user.id

    await context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
    await update.message.reply_text("Generating your personalized digest... I'll send it to you in a private message.")

    agent_request = "Create a personalized digest of recent community conversations for me."
    response_data = await state.api_client.execute_agent_task(agent_request, user_id)
    logger.debug(f"Received digest data from API for user {user_id}: {response_data}")
    
    reply = response_data.get("result") or response_data.get("error", "I couldn't generate your digest.")
    logger.info(f"Sending proactive intervention message to chat {update.effective_chat.id}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply, parse_mode='Markdown')

# --- Message & Media Handlers ---
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Handling text message from user {update.effective_user.id} in chat {update.effective_chat.id}")
    state: BotState = context.application.bot_data['state']
    message = update.message
    text = message.text or message.caption
    chat_id = update.effective_chat.id
    user_id = message.from_user.id
    logger.debug(f"Message details: chat_id={chat_id}, user_id={user_id}, text='{text[:50]}...'")

    # Record all messages for context, but only respond when addressed
    if chat_id not in state.chat_trackers:
        state.chat_trackers[chat_id] = ChatTracker()
    tracker = state.chat_trackers[chat_id]
    tracker.messages.append({'user': message.from_user.first_name, 'text': text, 'role': 'user'})
    tracker.message_count_since_last_check += 1

    # Determine if the bot should respond
    is_private_chat = message.chat.type == ChatType.PRIVATE
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.username == BOT_USERNAME
    is_mentioning_bot = BOT_USERNAME and f'@{BOT_USERNAME}' in text

    should_respond = is_private_chat or is_reply_to_bot or is_mentioning_bot

    if tracker.message_count_since_last_check >= PROACTIVE_MESSAGE_THRESHOLD:
        await check_proactive_intervention(update, context)
        tracker.message_count_since_last_check = 0
        # Don't return, allow proactive check and normal response if addressed

    if should_respond:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        history = list(tracker.messages)
        # Ensure we call the correct chat endpoint, not the agent
        logger.info(f"Sending message from user {user_id} in chat {chat_id} to RAG pipeline")
        response_data = await state.api_client.chat(user_id, text, conversation_history=history)
        reply = response_data.get("response") or response_data.get("error", "I seem to have lost my train of thought.")
        bot_reply = await update.message.reply_text(reply)
        # Add the bot's response to the history for true multi-turn chat
        if 'error' not in response_data:
            tracker.messages.append({'user': BOT_USERNAME, 'text': bot_reply.text, 'role': 'assistant'})

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Received /upload command from user {update.effective_user.id} in chat {update.effective_chat.id}")
    """Handles the /upload command, requiring a file caption."""
    state: BotState = context.application.bot_data['state']
    message = update.message
    user_id = message.from_user.id

    media_obj = message.document or (message.photo[-1] if message.photo else None)

    if not media_obj or not message.caption or '/upload' not in message.caption:
        await message.reply_text("To upload a file, please send the file and use `/upload` as the caption.")
        return

    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOADING_DOCUMENT)

    try:
        file_id = media_obj.file_id
        file = await context.bot.get_file(file_id)
        
        filename = getattr(media_obj, 'file_name', f"{file.file_id}.jpg")
        mime_type = getattr(media_obj, 'mime_type', 'image/jpeg')
        file_size = getattr(media_obj, 'file_size', 0)

        logger.info(f"Processing file upload: name={filename}, type={mime_type}, size={file_size} bytes")

        file_bytes = await file.download_as_bytearray()

        # Check for supported file types for documents
        if message.document and mime_type not in SUPPORTED_FILE_TYPES:
            await message.reply_text(f"Sorry, I can only process PDF, TXT, or Markdown files. Your file is a `{mime_type}`.")
            return

        # Ensure we call the correct file ingestion endpoint
        logger.info(f"Sending file '{filename}' to ingestion API for user {user_id}")
        response_data = await state.api_client.ingest_file(file_bytes, filename, user_id)
        reply = response_data.get("message") or response_data.get("error", "File ingestion failed.")

        logger.info(f"Sending ingestion response to chat {message.chat_id}")
        await message.reply_text(reply)
    except Exception as e:
        logger.exception(f"Error during media upload for user {user_id}: {e}")
        await message.reply_text("An error occurred while processing your file.")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Acknowledge the button press
    logger.info(f"Received button callback from user {query.from_user.id} with data: {query.data}")

    action, *params = query.data.split(':')
    
    if action == 'summarize_proactive' or action == 'find_docs_proactive':
        await handle_user_proactive_action(query, context, action)
    elif action == 'kb_approve' or action == 'kb_reject':
        await handle_admin_kb_action(query, context, action, params)
    else:
        await query.edit_message_text(text="Sorry, I don't know how to handle that action.")

# --- Proactive & Admin Logic (largely unchanged) ---
async def check_proactive_intervention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Checking for proactive intervention in chat {update.effective_chat.id}")
    state: BotState = context.application.bot_data['state']
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    tracker = state.chat_trackers.get(chat_id)

    if not tracker or not tracker.messages:
        return

    logger.info(f"Checking for proactive intervention in chat {chat_id}")
    conversation_history = "\n".join(f"{msg['user']}: {msg['text']}" for msg in tracker.messages)
    
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

        if kb_draft:
            logger.debug(f"KB draft created with confidence: {kb_draft.get('confidence_score', 0)}")
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
    logger.info(f"Sending knowledge base draft for approval to admin chat {ADMIN_CHAT_ID}")
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID is not set. Cannot send KB draft for approval.")
        return

    state: BotState = context.application.bot_data['state']
    draft_id = str(uuid.uuid4())
    state.kb_drafts[draft_id] = kb_draft

    title = kb_draft.get('title', 'Untitled')
    content = kb_draft.get('content', '')
    message_text = f"**New Knowledge Base Draft**\n\n**Title:** {title}\n\n**Content:**\n{content[:1000]}..."

    keyboard = [
        [InlineKeyboardButton("Approve", callback_data=f'kb_approve:{draft_id}')],
        [InlineKeyboardButton("Reject", callback_data=f'kb_reject:{draft_id}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    logger.info(f"Sent KB draft {draft_id} for admin approval.")

async def handle_user_proactive_action(query: Update.callback_query, context: ContextTypes.DEFAULT_TYPE, action: str):
    logger.info(f"Handling user proactive action '{action}' from user {query.from_user.id}")
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
    logger.info(f"Handling admin KB action '{action}' from user {query.from_user.id}")
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
            await query.edit_message_text(text=f"Approved and ingested draft '{title}'.")
            logger.info(f"Admin {user_id} approved KB draft {draft_id}.")
        except Exception as e:
            logger.exception(f"Failed to ingest approved KB article {draft_id}: {e}")
            await query.edit_message_text(text="Failed to ingest the article. See logs for details.")
    
    elif action == 'kb_reject':
        state.kb_drafts.pop(draft_id)
        await query.edit_message_text(text="Rejected draft.")
        logger.info(f"Admin {user_id} rejected KB draft {draft_id}.")

# --- Main Application Setup ---
async def post_init(application: Application):
    if not BOT_USERNAME:
        logger.error("BOT_USERNAME environment variable not set. The bot may not behave as expected in groups.")
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID environment variable not set. KB approval workflow is disabled.")
    api_client = ApiClient()
    application.bot_data['state'] = BotState(api_client)
    logger.info("Bot state initialized with ApiClient.")

async def on_shutdown(application: Application):
    state: BotState = application.bot_data.get('state')
    if state and state.api_client:
        await state.api_client.close()
        logger.info("ApiClient session closed.")

def main():
    logger.info("Starting bot...")

    app = Application.builder()\
        .token(TOKEN)\
        .post_init(post_init)\
        .build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler(['summarize', 'extract_actions', 'highlights'], contextual_agent_command))
    app.add_handler(CommandHandler('digest', digest_command))
    app.add_handler(CommandHandler('upload', upload_command))

    # Message & Callback Handlers
    # The upload_command now handles media, so the generic handlers are removed.
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    # We also need a handler for captioned media that are NOT commands
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_text_message))
    app.add_handler(CallbackQueryHandler(button_callback_handler))

    app.add_post_shutdown(on_shutdown)

    logger.info("Bot is polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
