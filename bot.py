import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein (jaise 🧲 mechanics ke liye, 🧬 biology ke liye, 💡 tricks ke liye, ⚡ electricity ke liye).
3. Direct answer dene ke bajaye, step-by-step samjhayein.
4. Jahaan zaroori ho, wahan text-based diagrams ya clear visual descriptions provide karein taaki student imagine kar sake.
5. Agar koi question mushkil hai, toh use aasan parts mein break karein.
"""

model = genai.GenerativeModel(
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
        response = model.generate_content(user_question)
        await processing_msg.edit_text(response.text)
    except Exception as e:
        print(f"Text Error: {e}")
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Image ko read karke solution nikal raha hoon... ⚙️")
    
    try:
        # Check karna ki message mein photo hai ya nahi (Forwarded cases ke liye safety check)
        message = update.message
        if not message.photo:
            await processing_msg.edit_text("Mujhe is message mein koi image nahi mili 😔. Please direct gallery se attach karke bhejein.")
            return

        # Sabse highest resolution wali photo select karna
        photo = message.photo[-1]
        photo_file = await photo.get_file()
        
        # Bytes download karna
        image_bytes = await photo_file.download_as_bytearray()
        
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": bytes(image_bytes)
            }
        ]
        
        prompt = "Is image mein diye gaye question ko dekho, solve karo aur step-by-step fully explain karo."
        response = model.generate_content([prompt, image_parts[0]])
        
        await processing_msg.edit_text(response.text)
        
    except Exception as e:
        # Yeh print Railway logs mein dikhega taaki hume real error pata chale
        print(f"CRITICAL IMAGE ERROR: {str(e)}")
        await processing_msg.edit_text("Mujhe is image ko read karne mein problem ho rahi hai 😔. Kya aap thodi clear photo bhej sakte hain?")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return
        
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    print("Bot is starting on Railway... 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
