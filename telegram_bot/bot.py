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
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user_id: int = update.message.from_user.id

    print(f'User ({user_id}) in {message_type}: "{text}"')

    processed_text: str = text.lower()
    response_data = {}

    if 'filter' in processed_text:
        response_data = await client.post_to_backend("filter", text, user_id)
        reply = response_data.get("filtered", "No filtered result found.")
    elif 'query' in processed_text or 'what' in processed_text or 'when' in processed_text or 'how' in processed_text:
        response_data = await client.post_to_backend("query", text, user_id)
        reply = response_data.get("response", "No query response found.")
    elif 'hello' in processed_text or 'hi' in processed_text:
        reply = "Hello! How can I help you?"
    else:
        reply = "I do not understand what you wrote..."

    if response_data.get("error"):
        reply = response_data["error"]

    print(f'Bot: "{reply}"')
    await update.message.reply_text(reply)

# --- Main Application Setup ---
if __name__ == '__main__':
    clear_webhook()

    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Polling...")
    app.run_polling(poll_interval=3)
