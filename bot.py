import os
import requests
import google.generativeai as genai
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Engines Configuration
genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein.
3. Direct answer dene ke bajaye, step-by-step samjhayein.
"""

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
    user_question = update.message.text
    processing_msg = await update.message.reply_text("🤔 Question analyze kar raha hoon... ⏳")
    try:
        response = gemini_model.generate_content(user_question)
        await processing_msg.edit_text(response.text)
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Processing shuru... ⚙️")
    
    try:
        # 1. Telegram File ID nikalna
        file_id = update.message.photo[-1].file_id
        
        # 2. Telegram API se direct File Path fetch karna via standard Requests (Bypasses library blocks)
        get_file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        file_info = requests.get(get_file_url).json()
        
        if not file_info.get("ok"):
            await processing_msg.edit_text("Telegram server se image ka link nahi mil pa raha hai 😔.")
            return
            
        file_path = file_info["result"]["file_path"]
        image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

        # 3. Groq ko direct URL pass karna
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
        print(f"Direct Network Method Error: {e}")
        await processing_msg.edit_text("Mujhe is image ko process karne mein abhi dikkat ho rahi hai 😔. Ek baar text mein poochiye.")

def main():
    if not TELEGRAM_BOT_TOKEN: return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(filters.TEXT & ~filters.COMMAND, handle_text_question)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))
    app.run_polling()

if __name__ == "__main__":
    main()
