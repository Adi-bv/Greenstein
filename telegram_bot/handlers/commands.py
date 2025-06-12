import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from ..client import ApiClient, logger
from . import history


def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parse mode."""
    # Chars to escape: '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([\\{re.escape(escape_chars)}])', r'\\\1', text)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    logger.info(f"Received /start command from user {update.effective_user.id}")
    await update.message.reply_text(
        'Hello! I am Greenstein, your AI community assistant. I can answer questions, '
        'summarize discussions, and help manage our knowledge base. '
        'Type /help to see all my commands.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /help command."""
    bot_username = context.bot.username
    logger.info(f"Received /help command from user {update.effective_user.id}")
    help_text = (
        "Here's what I can do:\n\n"
        f"💬 *Chat with me*: Mention `@{bot_username}` or reply to my messages in a group.\n\n"
        "🧠 *Agent Commands*:\n"
        " • `/summarize` - I'll summarize the recent conversation.\n"
        " • `/actions` - I'll find action items in the recent conversation.\n"
        " • `/highlights` - I'll give you the highlights of the recent conversation.\n\n"
        "📄 *Knowledge Base*:\n"
        " • `/upload` - Reply to a file with this command to add it to our knowledge base.\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def agent_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic handler for agent commands that operate on conversation history."""
    api_client: ApiClient = context.application.bot_data['api_client']
    command = update.message.text.split(' ')[0][1:].replace('_', ' ')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text

    # Add the user's command to history for context
    history.add_message_to_history(chat_id, user_name, message_text)

    logger.info(f"Received agent command `/{command}` from user {user_id} in chat {chat_id}")

    conversation_history = history.get_conversation_history(chat_id)
    if not conversation_history:
        await update.message.reply_text("There's no conversation history yet.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Frame the request for the agent
    agent_request = f"Based on the following conversation, please {command}:\n\n---\n{conversation_history}\n---"

    response_data = await api_client.execute_agent_task(agent_request)

    if "error" in response_data:
        reply = response_data["error"]
    else:
        result = response_data.get("result", f"I couldn't perform the `/{command}` action right now.")
        reply = escape_markdown_v2(str(result))

    # Add the bot's response to history
    history.add_message_to_history(chat_id, "Greenstein", reply)

    logger.info(f"Sending reply for `/{command}` to chat {chat_id}")
    await update.message.reply_text(reply, parse_mode='MarkdownV2')
