import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Logging set up karein
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment variables uthayein
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client initialize karein
groq_client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Main aapka JEE/NEET assistant hoon. Poochhiye apna sawaal! Main aapko Hinglish mein samjhaunga. 👍")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        # Chat completion jisme Hinglish ke liye system instruction add kiya hai
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant for JEE/NEET students. Always reply in easy-to-understand Hinglish (mix of Hindi and English like conversational chat). Explain complex physics, chemistry, and biology concepts in simple terms using points, so that Indian students can understand easily."
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        reply = chat_completion.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        await update.message.reply_text("❌ Error aayi, dobara try karein.")

def main():
    if not TOKEN or not GROQ_API_KEY:
        logging.error("Variables missing!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot chal raha hai...")
    application.run_polling()

if __name__ == '__main__':
    main()
