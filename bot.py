import os
import logging
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup taaki Railway dashboard par error saaf dikhe
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Client Initialization
groq_client = Groq(api_key=GROQ_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein.
3. Direct answer dene ke bajaye, step-by-step samjhayein.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Hello! 👋 Main aapka Personal JEE/NEET Expert Tutor hoon! 🎓\n\n"
        "Aap mujhe text ya photo mein questions bhej sakte hain. Let's crack it! 🚀"
    )
    await update.message.reply_text(welcome_msg)

async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    processing_msg = await update.message.reply_text("🤔 Question analyze kar raha hoon... thoda wait karein ⏳")
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_question}
            ],
            model="llama-3.2-11b-vision-preview",
        )
        solution_text = chat_completion.choices[0].message.content
        await processing_msg.edit_text(solution_text)
    except Exception as e:
        logging.error(f"Text Error: {e}")
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Scanner active kar raha hoon... ⚙️")
    
    try:
        # Telegram internal helper se async tareeqe se image path fetch karna
        photo = update.message.photo[-1]
        file_info = await context.bot.get_file(photo.file_id)
        image_url = file_info.file_path

        logging.info(f"Successfully retrieved image URL: {image_url}")

        # Groq Multimodal Vision API Request
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is image mein diye gaye JEE/NEET ke question ko dekho, solve karo aur step-by-step fully explain karo."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        
        solution_text = chat_completion.choices[0].message.content
        await processing_msg.edit_text(solution_text)
        
    except Exception as e:
        logging.error(f"Vision Error: {e}")
        await processing_msg.edit_text("Mujhe is image ko process karne mein abhi thodi dikkat ho rahi hai 😔. Ek baar text mein pooch kar dekhiye!")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.critical("Error: TELEGRAM_BOT_TOKEN missing!")
        return
        
    # Modern Application Builder
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Core Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    logging.info("Master Bot running via polling... 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
