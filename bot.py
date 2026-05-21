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
    welcome_text = (
        "👋 Hello Dost! Main aapka personal JEE/NEET Assistant hoon. 🔥\n\n"
        "Main aapko saare complex topics **Hinglish, emojis** aur clear **text-based diagrams** ke sath samjhaunga.\n\n"
        "📝 Note: Main direct photo send nahi kar sakta, par agar aapko kisi topic ki image chahiye, toh main aapko uska direct secure reference link de dunga! 🌐"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        # Prompt tweaked to provide visual web links or text-art diagrams
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert AI tutor for JEE/NEET. Reply in easy conversational Hinglish with emojis. "
                        "If the user asks for an image, picture, or diagram of a scientific concept (like cell, atom, plant tissue, etc.), "
                        "you cannot send direct files, so you must:\n"
                        "1. Create a clear ASCII/Text-based neat block diagram using characters if possible.\n"
                        "2. Provide a clean markdown web search link for that image (e.g., [Click here to see Diagram](https://commons.wikimedia.org/w/index.php?search=concept_name)) so they can click and see the exact picture instantly."
                    )
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        reply = chat_completion.choices[0].message.content
        await update.message.reply_text(reply, parse_mode="Markdown", disable_web_page_preview=False)
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        await update.message.reply_text("❌ Oops! Kuch error aayi. Ek baar dobara try karo bro.")

def main():
    if not TOKEN or not GROQ_API_KEY:
        logging.error("Variables missing!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Image Link Supported Bot chal raha hai...")
    application.run_polling()

if __name__ == '__main__':
    main()
