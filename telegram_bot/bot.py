import os
import sys
from dotenv import load_dotenv
from typing import Final, List

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.ext.filters import Document

from .client import ApiClient, logger
from .handlers import commands, messages, media

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
TOKEN: Final = os.getenv("TELEGRAM_TOKEN")
AGENT_COMMANDS: Final[List[str]] = ['summarize', 'actions', 'highlights']

# --- Application Lifecycle Hooks ---
async def post_init(application: Application):
    """Initializes the ApiClient and stores it in the bot_data context."""
    if not TOKEN:
        logger.critical("TELEGRAM_TOKEN environment variable not set. Exiting.")
        sys.exit(1) # Exit with a non-zero status code to indicate an error

    api_client = ApiClient()
    application.bot_data['api_client'] = api_client
    logger.info("Bot application initialized with ApiClient.")

async def on_shutdown(application: Application):
    """Gracefully closes the ApiClient session on bot shutdown."""
    logger.info("Bot is shutting down...")
    api_client: ApiClient = application.bot_data.get('api_client')
    if api_client:
        await api_client.close()
        logger.info("ApiClient session closed successfully.")

# --- Main Application Setup ---
def main():
    """Sets up and runs the Telegram bot."""
    logger.info("Starting bot...")

    # Create the Telegram Application
    app = Application.builder()\
        .token(TOKEN)\
        .post_init(post_init)\
        .post_shutdown(on_shutdown)\
        .build()

    # --- Register Command Handlers ---
    app.add_handler(CommandHandler('start', commands.start_command))
    app.add_handler(CommandHandler('help', commands.help_command))
    
    # Register agent commands
    app.add_handler(CommandHandler(AGENT_COMMANDS, commands.agent_command_handler))

    # --- Register Media and Message Handlers ---
    # Handler for the /upload command (must be a reply to a document)
    app.add_handler(CommandHandler('upload', media.upload_command, filters=filters.REPLY & Document.ALL))

    # Handler for general text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages.handle_text_message))

    # Start polling for updates
    logger.info("Bot is now polling for updates...")
    try:
        app.run_polling()
    except Exception as e:
        logger.critical(f"Bot polling failed with an unhandled exception: {e}", exc_info=True)
        # In a real scenario, you might want to implement a restart mechanism here.

if __name__ == '__main__':
    main()
