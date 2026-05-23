import os
import logging
import io
import google.generativeai as genai
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup for Railway
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# AI Engines Configure karna
genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein (jaise 🧲, 🧬, 💡, ⚡).
3. Direct answer dene ke bajaye, step-by-step samjhayein.
"""

# Gemini Model Image Ke Liye
gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_instruction
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Hello! 👋 Main aapka Personal JEE/NEET Expert Tutor hoon! 🎓\n\n"
        "Aap mujhe text ya photo mein questions bhej sakte hain. Let's crack it! 🚀"
    )
    await update.message.reply_text(welcome_msg)

async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text handler using Groq (Super Fast & Reliable)"""
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
        await processing_msg.edit_text(f"Oops! Technical issue: {str(e)[:50]}")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Photo handler using Gemini Direct Bytes (Bypasses all Groq 400 and Link blocks)"""
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Scanner active kar raha hoon... ⚙️")
    
    try:
        # 1. Telegram se photo direct memory buffer me download karna
        photo = update.message.photo[-1]
        file_info = await context.bot.get_file(photo.file_id)
        
        out = io.BytesIO()
        await file_info.download_to_memory(out)
        image_bytes = out.getvalue()

        logging.info("Image bytes downloaded successfully for Gemini.")

        # 2. Gemini native content format taiyar karna (No Base64 URL issue, No domain block)
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": image_bytes
            }
        ]
        
        prompt = "Is image mein diye gaye JEE/NEET ke question ko dekho, solve karo aur step-by-step fully explain karo."

        # 3. Gemini Call
        response = gemini_model.generate_content([prompt, image_parts[0]])
        
        await processing_msg.edit_text(response.text)
        
    except Exception as e:
        logging.error(f"Gemini Vision Error Details: {e}")
        await processing_msg.edit_text(f"Technical Issue details: {str(e)[:60]}")

def main():
    if not TELEGRAM_BOT_TOKEN:
        logging.critical("TELEGRAM_BOT_TOKEN missing!")
        return
        
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    logging.info("Hybrid Ultimate Bot is online and stable... 🚀")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
