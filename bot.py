import os
import requests
import base64
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot active! Photo ya Text bhejo.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("Analyzing... 🔍")
    try:
        # Step 1: Get image
        file = await update.message.photo[-1].get_file()
        image_data = requests.get(file.file_path).content
        base64_image = base64.b64encode(image_data).decode('utf-8')

        # Step 2: Use the official v1beta model path
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Explain this physics diagram step-by-step."},
                    {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
                ]
            }]
        }
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        # Step 3: Check response
        if "candidates" in data:
            answer = data['candidates'][0]['content']['parts'][0]['text']
            await msg.edit_text(answer)
        else:
            # Ye part aapko batayega ki asli error kya hai
            await msg.edit_text(f"API Error! Detail: {str(data)[:100]}")

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)[:100]}")

def main():
    if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
        print("Missing API Keys!")
        return
        
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
