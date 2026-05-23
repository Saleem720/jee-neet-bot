import os
import requests
import base64
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot active! Photo bhejo.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Analyzing... 🔍")
    try:
        # File Download
        file = await update.message.photo[-1].get_file()
        image_data = requests.get(file.file_path, timeout=10).content
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Google API Request with explicit timeout
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [
                {"text": "Solve step-by-step."},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
            ]}]
        }
        
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()
        
        if "candidates" in data:
            answer = data['candidates'][0]['content']['parts'][0]['text']
            await msg.edit_text(answer)
        else:
            await msg.edit_text(f"API Data: {str(data)[:50]}")

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)[:50]}")

def main():
    # Railway ke liye timeout badhaya
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(30).write_timeout(30).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
