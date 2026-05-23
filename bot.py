import os
import requests
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq Engine Initialization
groq_client = Groq(api_key=GROQ_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein (jaise 🧲, 🧬, 💡, ⚡).
3. Direct answer dene ke bajaye, step-by-step samjhayein.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Hello! 👋 Main aapka Personal JEE/NEET Expert Tutor hoon! 🎓\n\n"
        "Aap mujhe apne doubts text mein bhej sakte hain, ya phir question ki photo 📸 bhej sakte hain. "
        "Aaiye milkar padhai shuru karte hain! 🚀"
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
        print(f"Text Error: {e}")
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Scanner active kar raha hoon... ⚙️")
    
    try:
        # 1. Telegram File ID extract karna
        file_id = update.message.photo[-1].file_id
        
        # 2. Direct Web API requests se File Path fetch karna
        get_file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        response = requests.get(get_file_url)
        file_info = response.json()
        
        if not file_info.get("ok"):
            await processing_msg.edit_text("Telegram server se image verify nahi ho pa rahi hai 😔.")
            return
            
        file_path = file_info["result"]["file_path"]
        image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"

        # 3. Groq Llama Vision API Request
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
        print(f"Vision Error: {e}")
        await processing_msg.edit_text("Mujhe is image ko process karne mein abhi thodi dikkat ho rahi hai 😔. Ek baar text mein pooch kar dekhiye!")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return
        
    # Standard v20 Builder Loop
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Base Core Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    print("Master Bot is starting... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
