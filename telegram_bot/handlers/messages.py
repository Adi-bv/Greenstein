from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from ..client import ApiClient, logger
from . import history

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages, either direct or in groups."""
    api_client: ApiClient = context.application.bot_data['api_client']
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text

    # Add user's message to history
    history.add_message_to_history(chat_id, user_name, message_text)

    # Decide if the bot should reply
    # It replies if it's a private message or if the bot is mentioned/replied to in a group.
    should_reply = (
        update.message.chat.type == 'private' or
        (context.bot.username in message_text) or
        (update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)
    )

    if not should_reply:
        logger.debug(f"Ignoring message in chat {chat_id} as it doesn't warrant a reply.")
        return

    logger.info(f"Handling text message from user {user_id} in chat {chat_id}")
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Get chat response from the backend
    response_data = await api_client.get_chat_response(message=message_text, user_id=user_id)
    
    reply = response_data.get("response") or response_data.get("error", "Sorry, I had trouble thinking of a response.")

    # Add bot's response to history
    history.add_message_to_history(chat_id, "Greenstein", reply)

    logger.info(f"Sending chat response to user {user_id} in chat {chat_id}")
    await update.message.reply_text(reply)
