from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from ..client import ApiClient, logger
from . import history

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming text messages, responding in DMs, replies, or mentions."""
    message = update.effective_message
    chat = update.effective_chat
    bot = context.bot

    # Determine if the bot should respond.
    # It should respond in private chats, or when replied to, or when mentioned in a group.
    should_respond = False
    if chat.type == 'private':
        should_respond = True
    elif message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        should_respond = True
    elif f"@{bot.username}" in message.text:  # Check for an explicit mention
        should_respond = True

    if not should_respond:
        logger.debug(f"Ignoring message in chat {chat.id} as it was not a direct interaction.")
        return

    api_client: ApiClient = context.application.bot_data['api_client']
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text

    # Add user's message to history for context
    history.add_message_to_history(chat_id, user_name, message_text)

    logger.info(f"Handling text message from user {user_id} in chat {chat_id}")
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Get chat response from the backend
    response_data = await api_client.get_chat_response(message=message_text, user_id=user_id)
    
    reply = response_data.get("response") or response_data.get("error", "Sorry, I had trouble thinking of a response.")

    # Add bot's response to history
    history.add_message_to_history(chat_id, "Greenstein", reply)

    logger.info(f"Sending chat response to user {user_id} in chat {chat_id}")
    await update.message.reply_text(reply)
