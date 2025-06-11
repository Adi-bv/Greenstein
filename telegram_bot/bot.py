import os
from dotenv import load_dotenv
from typing import Final
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from . import client

# Load environment variables
load_dotenv()

TOKEN: Final = os.getenv("TELEGRAM_TOKEN", "7905624830:AAEGDOfk0ppuW8_Rsn0NVMjbVXt8IJNNsaQ")
BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "greenstein_bot")

def clear_webhook():
    async def _clear():
        bot = Bot(token=TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
    asyncio.run(_clear())

# --- Command Handlers ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am Greenstein Bot. How can I assist you today?')

# --- Message Processing ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all non-command text messages by forwarding them to the backend."""
    text: str = update.message.text
    user_id: int = update.message.from_user.id

    print(f'User ({user_id}) sent: "{text}"')

    # Send the message to the backend and get the AI's response
    response_data = await client.get_chat_response(text, user_id)

    # Extract the reply or the error message
    reply = response_data.get("response") or response_data.get("error")

    if not reply:
        reply = "I seem to have lost my train of thought. Could you try that again?"

    print(f'Bot responding: "{reply}"')
    await update.message.reply_text(reply)

# --- Main Application Setup ---
if __name__ == '__main__':
    # clear_webhook()

    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Polling...")
    app.run_polling(poll_interval=3)
