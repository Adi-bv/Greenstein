import httpx
import re 

from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN: Final = '7905624830:AAEGDOfk0ppuW8_Rsn0NVMjbVXt8IJNNsaQ'
BOT_USERNAME: Final = 'greenstein_bot'

BACKEND_URL = "http://127.0.0.1:8000"

#Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am Greenstein Bot. How can I assist you today?')



# Responses
async def handel_response(text: str) -> str:
  processed: str = text.lower()
  if 'filter' in processed:
    async with httpx.AsyncClient() as client:
      res = await client.post(f"{BACKEND_URL}/filter", json={"message": text})
      return res.json().get("filtered", "No filtered result found.")
    
  elif 'summary' in processed or 'summarize' in processed:
    async with httpx.AsyncClient() as client:
            res = await client.post(f"{BACKEND_URL}/summary", json={"message": text})
            return res.json().get("summarized", "No summary response found.")
        
  elif 'query' in processed or 'what' in processed or 'when' in processed or 'how' in processed:
    async with httpx.AsyncClient() as client:
            res = await client.post(f"{BACKEND_URL}/query", json={"message": text})
            return res.json().get("response", "No query response found.")
          
    
  elif 'hello' in processed or 'hi' in processed:
        return "Hello! How can I help you?"

  return "I do not understand what you wrote..."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    text_lower = text.lower()

    print(f'User({update.message.chat.id}) in {message_type}: "{text}"')
    print(f'Message type: {message_type}, Text: "{text}", Contains bot name: {"@"+BOT_USERNAME.lower() in text_lower}')

    if message_type in ['group', 'supergroup']:
        if re.search(f"@{BOT_USERNAME}", text, re.IGNORECASE):
          clean_text = re.sub(f"@{BOT_USERNAME}", "", text, flags=re.IGNORECASE).strip()
        else:
          return
    else:
        clean_text = text_lower

    # Call appropriate backend endpoint
    # Use the central response logic
    result = await handel_response(clean_text)


    await update.message.reply_text(result)
  
  
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    
if __name__ == '__main__':
    print('Starting Greenstein Bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    # Only handle private messages or group messages mentioning the bot
    app.add_handler(MessageHandler(
    filters.TEXT & (filters.ChatType.PRIVATE | filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
    handle_message
))

    # Errors
    app.add_error_handler(error)
    # Polls the bot
    print('Polling....')
    app.run_polling(poll_interval=3)