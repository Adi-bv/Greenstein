import telegram
from textwrap import dedent
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from telegram.helpers import escape_markdown

from ..client import ApiClient, logger
from .. import history


def escape_markdown_v2(text: str) -> str:
    """Escapes text for MarkdownV2 using the official python-telegram-bot helper."""
    return escape_markdown(str(text), version=2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    logger.info(f"Received /start command from user {update.effective_user.id}")
    text = (
        'Hello! I am Greenstein, your AI community assistant. I can answer questions, '
        'summarize discussions, and help manage our knowledge base. '
        'Type /help to see all my commands.'
    )
    # Sending as plain text to avoid any parsing issues.
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays a help message with all available commands."""
    bot_username = context.bot.username
    # Simple plain text help message to avoid parsing errors.
    help_text = dedent(f"""
        Here's what I can do for you:

        Proactive Chat:
        In any group, mention @{bot_username} or reply to one of my messages to chat with me.

        General Commands:
        /start - Welcome message
        /help - Shows this help message

        Knowledge Management:
        /upload - Upload a document (reply to a file)

        Agent Commands (analyze chat history):
        /report - Get a detailed report of the chat
        /tldr - Get a very short summary
        /actions - Extract action items

        Utility Commands:
        /id - Get chat and user IDs

        Admin Commands:
        /announcement <brief> - Broadcast to groups you admin (admin only, private chat)
    """)
    await update.message.reply_text(help_text)


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the current chat ID and user ID."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if update.effective_chat.type == 'private':
        await update.message.reply_text(f"Your User ID is: {user_id}")
    else:
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            # Plain text list of admins to avoid parsing errors.
            admin_list = "\n".join([f"- {admin.user.id} ({admin.user.full_name})" for admin in admins])
            message = (
                f"Chat Information\n"
                f"- Chat ID: {chat_id}\n"
                f"- Your User ID: {user_id}\n\n"
                f"Group Admins:\n{admin_list}"
            )
            await update.message.reply_text(message)
        except Exception as e:
            logger.error(f"Could not fetch admins for chat {chat_id}: {e}")
            await update.message.reply_text(f"Chat ID: {chat_id}\nYour User ID: {user_id}")


async def agent_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generic handler for agent commands that operate on conversation history."""
    api_client: ApiClient = context.application.bot_data['api_client']
    command = update.message.text.split(' ')[0][1:]  # Get command without '/'
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    message_text = update.message.text

    # Add the user's command to history for context
    history.add_message_to_history(chat_id, user_name, message_text)

    logger.info(f"Received agent command `/{command}` from user {user_id} in chat {chat_id}")

    conversation_history = history.get_conversation_history(chat_id)
    if not conversation_history:
        await update.message.reply_text(escape_markdown_v2("There's no conversation history for me to work with yet."), parse_mode='MarkdownV2')
        return

    # Define specific prompts for each agent command
    agent_prompts = {
        'report': (
            "You are an analysis assistant. Please generate a comprehensive and detailed report on the following conversation. "
            "Include key discussion points, chronological events, decisions made, and any unresolved questions. Include any and all numerical figures, values and proper nouns. Use the conversation below as context:\n\n"
            "---\n"
            f"{conversation_history}\n"
            "---"
        ),
        'tldr': (
            "You are a summarization assistant. Provide a clear, concise TL;DR summary of the following conversation. "
            "Highlight the main outcomes and critical points discussed, capturing the essence of the dialogue. Keep the response very short "
            "Base your summary solely on the transcript below:\n\n"
            "---\n"
            f"{conversation_history}\n"
            "---"
        ),
        'actions': (
            "You are an extraction assistant. Identify and list all actionable items from the following conversation. "
            "Include tasks, deadlines, assignments, or decisions that require follow-up. Return the list of actions "
            "in bullet points. Analyze the conversation context provided below:\n\n"
            "---\n"
            f"{conversation_history}\n"
            "---"
        )
    }
    agent_request = agent_prompts.get(command)
    if not agent_request:
        logger.warning(f"Unknown agent command `/{command}` received from user {user_id}.")
        return  # Ignore unknown commands silently

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    response_data = await api_client.execute_agent_task(agent_request)

    if "error" in response_data:
        reply_text = response_data["error"]
        history.add_message_to_history(chat_id, "Greenstein", reply_text)
    else:
        reply_text = response_data.get("result", f"I couldn't perform the `/{command}` action right now.")
        history.add_message_to_history(chat_id, "Greenstein", reply_text)

    logger.info(f"Sending reply for `/{command}` to chat {chat_id}")
    # The reply_text is dynamic content from the API and must be escaped.
    await update.message.reply_text(escape_markdown_v2(reply_text), parse_mode='MarkdownV2')


async def announcement_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /announcement command for the admin.

    Generates an announcement from a brief and broadcasts it to all configured
    chats where the admin user is also an administrator.
    """
    admin_user_id = context.application.bot_data.get('admin_user_id')
    announcement_chat_ids = context.application.bot_data.get('announcement_chat_ids', [])
    user_id = update.effective_user.id

    if str(user_id) != admin_user_id:
        await update.message.reply_text(escape_markdown_v2("Sorry, this command is for admins only."), parse_mode='MarkdownV2')
        return

    if not announcement_chat_ids:
        await update.message.reply_text(escape_markdown_v2("There are no announcement channels configured."), parse_mode='MarkdownV2')
        return

    brief = ' '.join(context.args)
    if not brief:
        await update.message.reply_text(escape_markdown_v2("Please provide a brief for the announcement.\nUsage: `/announcement <your brief here>`"), parse_mode='MarkdownV2')
        return

    logger.info(f"Admin {user_id} initiated an announcement with brief: '{brief}'")
    await update.message.reply_text(escape_markdown_v2(f"Generating announcement and checking permissions for {len(announcement_chat_ids)} group(s)..."), parse_mode='MarkdownV2')
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    api_client: ApiClient = context.application.bot_data['api_client']
    prompt = f"Based on the following brief, draft a professional announcement. Use Telegram's MarkdownV2 syntax.\n\n**Brief:**\n{brief}"

    response_data = await api_client.execute_agent_task(prompt)

    if "error" in response_data:
        await update.message.reply_text(escape_markdown_v2(f"Sorry, I couldn't generate the announcement. Error: {response_data['error']}"), parse_mode='MarkdownV2')
        return

    generated_announcement = response_data.get("result", "Failed to generate announcement.")

    success_count, failed_chats, skipped_chats = 0, [], []

    for chat_id in announcement_chat_ids:
        try:
            chat_admins = await context.bot.get_chat_administrators(chat_id)
            if not any(admin.user.id == user_id for admin in chat_admins):
                logger.warning(f"Skipping chat {chat_id}: user {user_id} is not an admin.")
                skipped_chats.append(str(chat_id))
                continue

            # The announcement is pre-formatted as MarkdownV2 by the API, so it should not be escaped.
            await context.bot.send_message(chat_id=chat_id, text=generated_announcement, parse_mode='MarkdownV2')
            success_count += 1
            logger.info(f"Successfully sent announcement to chat {chat_id}.")
        except Exception as e:
            logger.error(f"Failed to send to chat {chat_id}: {e}")
            failed_chats.append(str(chat_id))

    report_lines = []
    if success_count > 0:
        report_lines.append(f"✅ Announcement sent to {success_count} group(s).")
    if skipped_chats:
        report_lines.append(f"Skipped {len(skipped_chats)} group(s) where you aren't an admin: {', '.join(skipped_chats)}")
    if failed_chats:
        report_lines.append(f"⚠️ Failed to send to {len(failed_chats)} group(s): {', '.join(failed_chats)}")

    # Send final report as plain text to avoid parsing errors.
    final_report = '\n'.join(report_lines) or "Could not send to any groups."
    await update.message.reply_text(final_report)
