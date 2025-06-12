from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

from ..client import ApiClient, logger

SUPPORTED_MIME_TYPES = ['application/pdf', 'text/plain', 'text/markdown']

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /upload command for adding files to the knowledge base."""
    api_client: ApiClient = context.application.bot_data['api_client']
    user_id = update.effective_user.id
    
    logger.info(f"Received /upload command from user {user_id}")

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("Please reply to a document with the `/upload` command to add it to the knowledge base.")
        return

    document = update.message.reply_to_message.document
    
    if document.mime_type not in SUPPORTED_MIME_TYPES:
        await update.message.reply_text(f"Sorry, I can only process the following file types: PDF, TXT, MD. The provided file is of type '{document.mime_type}'.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
    
    try:
        # Download the file content
        file = await document.get_file()
        file_content = await file.download_as_bytearray()
        
        logger.info(f"Ingesting file '{document.file_name}' for user {user_id}")
        
        response = await api_client.ingest_file(
            file_content=bytes(file_content),
            filename=document.file_name,
            user_id=user_id
        )
        
        reply_text = response.get("message") or response.get("error", "An unknown error occurred during ingestion.")
        await update.message.reply_text(reply_text)
        
    except Exception as e:
        logger.exception(f"Error during file upload process for user {user_id}: {e}")
        await update.message.reply_text("An unexpected error occurred while trying to upload the file. Please try again later.")
