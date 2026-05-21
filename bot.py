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
        "Ab se main aapko saare complex topics ekdam mast **Hinglish** mein, "
        "lots of **emojis** 🎉 aur **diagrams/charts** ke sath samjhaunga.\n\n"
        "📚 Jo bhi doubt ho (Physics 🌌, Chemistry 🧪, Biology 🧬), bas yahan type karo!"
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        # Groq API Call with strict system instructions for Emojis + Hinglish + Structure
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert, friendly AI tutor for Indian students preparing for JEE and NEET exams. "
                        "Your job is to explain complex scientific concepts in a highly engaging way. "
                        "Strictly follow these rules:\n"
                        "1. ALWAYS reply in easy conversational Hinglish (Hindi + English mix).\n"
                        "2. Use plenty of relevant Emojis throughout the text to make it visually engaging and fun.\n"
                        "3. Break down heavy answers into bullet points, clear headings, and markdown tables where applicable.\n"
                        "4. Whenever explaining a structure, cycle, or mechanism (like cell structure, chemical bonds, physics laws), "
                        "describe a clear text-based mental diagram or comparison to help them visualize it easily."
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
        await update.message.reply_text(reply)
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
    
    print("Super Bot chal raha hai...")
    application.run_polling()

if __name__ == '__main__':
    main()
