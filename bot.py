import os
import google.generativeai as genai
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# AI Engines Configuration
genai.configure(api_key=GEMINI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein (jaise 🧲 mechanics ke liye, 🧬 biology ke liye, 💡 tricks ke liye, ⚡ electricity ke liye).
3. Direct answer dene ke bajaye, step-by-step samjhayein.
4. Jahaan zaroori ho, wahan text-based diagrams ya clear visual descriptions provide karein.
5. Agar koi question mushkil hai, toh use aasan parts mein break karein.
"""

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_instruction
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "Hello! 👋 Main aapka Personal JEE/NEET Expert Tutor hoon! 🎓\n\n"
        "Aap mujhe apne questions text mein bhej sakte hain, ya phir apne "
        "book/module se question ki photo 📸 click karke bhej sakte hain. "
        "Aaiye milkar in exams ko crack karein! 🚀"
    )
    await update.message.reply_text(welcome_msg)

async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text
    processing_msg = await update.message.reply_text("🤔 Question analyze kar raha hoon... thoda wait karein ⏳")
    try:
        response = gemini_model.generate_content(user_question)
        await processing_msg.edit_text(response.text)
    except Exception as e:
        print(f"Gemini Text Error: {e}")
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Scanner active kar raha hoon... ⚙️")
    
    try:
        # 1. Highest resolution photo object fetch karna
        photo_file = await update.message.photo[-1].get_file()
        
        # 2. Telegram API se strict URL structure taiyar karna
        # Agar file_path complete URL nahi hai, toh use standard link mein convert karna
        if photo_file.file_path and photo_file.file_path.startswith("http"):
            image_url = photo_file.file_path
        else:
            image_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{photo_file.file_path}"
        
        # 3. Groq Llama-3.2-Vision Engine ko image URL pass karna
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is image mein diye gaye JEE/NEET ke question ko dekho, solve karo aur step-by-step fully explain karo."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        
        solution_text = chat_completion.choices[0].message.content
        await processing_msg.edit_text(solution_text)
        
    except Exception as e:
        print(f"Vision Full Error Log: {e}")
        await processing_msg.edit_text("Mujhe is image ko process karne mein abhi thodi dikkat ho rahi hai 😔. Ek baar text mein pooch kar dekhiye!")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return
        
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    print("Hybrid URL-based Bot is starting on Railway... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
