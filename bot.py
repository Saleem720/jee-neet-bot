import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- API KEYS SETUP ---
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_TOKEN"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"

genai.configure(api_key=GEMINI_API_KEY)

# Hum Gemini model ko pehle hi bata rahe hain ki use kaise behave karna hai
# Yeh aapki "Expert, Emoji aur Diagram" waali requirement poori karega
system_instruction = """
Aap ek top-tier expert JEE aur NEET tutor hain. Aapka kaam students ke doubts solve karna hai.
Rules:
1. Hamesha friendly aur encouraging tone use karein.
2. Bahut saare relevant emojis use karein (jaise 🧲 mechanics ke liye, 🧬 biology ke liye, 💡 tricks ke liye, ⚡ electricity ke liye).
3. Direct answer dene ke bajaye, step-by-step samjhayein.
4. Jahaan zaroori ho, wahan text-based diagrams ya clear visual descriptions provide karein taaki student imagine kar sake.
5. Agar koi question mushkil hai, toh use aasan parts mein break karein.
"""

# Gemini 1.5 Flash use karenge kyunki yeh fast hai aur images bhi process karta hai
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_instruction
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab user /start command bhejta hai"""
    welcome_msg = (
        "Hello! 👋 Main aapka Personal JEE/NEET Expert Tutor hoon! 🎓\n\n"
        "Aap mujhe apne questions text mein bhej sakte hain, ya phir apne "
        "book/module se question ki photo 📸 click karke bhej sakte hain. "
        "Aaiye milkar in exams ko crack karein! 🚀"
    )
    await update.message.reply_text(welcome_msg)

async def handle_text_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Text waale questions ko solve karne ke liye"""
    user_question = update.message.text
    
    # User ko wait karne ka message
    processing_msg = await update.message.reply_text("🤔 Question analyze kar raha hoon... thoda wait karein ⏳")
    
    try:
        # Gemini AI se answer maangna
        response = model.generate_content(user_question)
        await processing_msg.edit_text(response.text)
    except Exception as e:
        await processing_msg.edit_text("Oops! Kuch technical issue aa gaya 😥. Thodi der baad try karein.")

async def handle_photo_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Images (Photo) waale questions ko solve karne ke liye"""
    processing_msg = await update.message.reply_text("📸 Photo mil gayi! Image ko read karke solution nikal raha hoon... ⚙️")
    
    try:
        # Telegram se highest resolution image download karna
        photo_file = await update.message.photo[-1].get_file()
        file_path = "temp_question.jpg"
        await photo_file.download_to_drive(file_path)
        
        # Image ko upload karke AI ko bhejna
        sample_file = genai.upload_file(path=file_path)
        
        prompt = "Is image mein diye gaye question ko solve karo aur step-by-step explain karo."
        response = model.generate_content([sample_file, prompt])
        
        await processing_msg.edit_text(response.text)
        
        # Temp file delete karna
        os.remove(file_path)
        
    except Exception as e:
        await processing_msg.edit_text("Mujhe is image ko read karne mein problem ho rahi hai 😔. Kya aap thodi clear photo bhej sakte hain?")

def main():
    """Bot ko start karne ka main function"""
    # Telegram app create karein
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers add karein
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_question))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_question))

    print("Bot is running... 🚀 (Press Ctrl+C to stop)")
    # Bot ko continuously run karna
    app.run_polling()

if __name__ == "__main__":
    main()
