from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
TOKEN: Final = '7905624830:AAEGDOfk0ppuW8_Rsn0NVMjbVXt8IJNNsaQ'
BOT_USERNAME: Final = 'greenstein_bot'

#Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! I am Greenstein Bot. How can I assist you today?')

    

# Responses

def handel_response(text: str) -> str:
  processed: str = text.lower()
  if 'hello' in processed or 'hi' in processed:
    return 'Hello! How can I help you?'
  return 'I do not understand what you wrote.....'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message_type: str= update.message.chat.type
  text: str = update.message.text
  
  print(f'User({update.message.chat.id}) in {message_type}: "{text}"')
  print(f'Message type: {message_type}, Text: "{text}", Contains bot name: {"@"+BOT_USERNAME.lower() in text.lower()}')

  
  if message_type=='group' or message_type=='supergroup':
    text = update.message.text.lower()
    if f'@{BOT_USERNAME.lower()}' in text:
      new_text: str = text.replace(BOT_USERNAME, '').strip()
      response: str = handel_response(new_text)
    else:
      return
  else:
    response: str = handel_response(text)
    
  print('Bot:',response)
  await update.message.reply_text(response)
  
  
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    
if __name__ == '__main__':
    print('Starting Greenstein Bot...')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    # Only handle private messages or group messages mentioning the bot
    app.add_handler(MessageHandler(
        filters.TEXT & (
            filters.ChatType.PRIVATE |
            (filters.ChatType.GROUP & filters.Update.MESSAGE & filters.Regex(f'@{BOT_USERNAME}'))
        ),
        handle_message
    ))
    # Errors
    app.add_error_handler(error)
    # Polls the bot
    print('Polling....')
    app.run_polling(poll_interval=3)