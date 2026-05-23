import os
import requests
import base64
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Logging ON kiya hai, Railway logs mein check karna
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
        logging.info("Image downloaded and encoded.")

        # Step 2: API Call
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [
                {"text": "Solve this JEE/NEET question."},
                {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}
            ]}]
        }
        
        response = requests.post(url, json=payload)
        logging.info(f"API Status: {response.status_code}")
        
        data = response.json()
        
        # Step 3: Extract answer
        if "candidates" in data:
            answer = data['candidates'][0]['content']['parts'][0]['text']
            await msg.edit_text(answer)
        else:
            logging.error(f"API Response Data: {data}")
            await msg.edit_text(f"API Error! Check Logs. Data: {str(data)[:50]}")

    except Exception as e:
        logging.error(f"CRITICAL ERROR: {e}")
        await msg.edit_text(f"Error: {str(e)[:50]}")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
