import os
import requests
import base64
import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def start(update, context):
    await update.message.reply_text("Bot is Ready! 🚀")

async def handle_photo(update, context):
    msg = await update.message.reply_text("Analyzing... 🔍")
    try:
        file = await update.message.photo[-1].get_file()
        image_data = requests.get(file.file_path, timeout=10).content
        base64_image = base64.b64encode(image_data).decode('utf-8')

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": "Solve this."}, {"inline_data": {"mime_type": "image/jpeg", "data": base64_image}}]}]}
        
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()
        
        answer = data['candidates'][0]['content']['parts'][0]['text']
        await msg.edit_text(answer)
    except Exception as e:
        await msg.edit_text(f"Error: {str(e)[:50]}")

if __name__ == '__main__':
    # Yeh part hi v21+ ke liye sahi hai
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Starting polling...")
    app.run_polling(drop_pending_updates=True)
