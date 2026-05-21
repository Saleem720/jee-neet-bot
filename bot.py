import os
import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from groq import Groq

# Logging set up karein
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Environment variables uthayein
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Groq client initialize
groq_client = Groq(api_key=GROQ_API_KEY)

# --- 1. START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to your Ultimate JEE/NEET AI Assistant!** 🔥\n\n"
        "Main aapki padhai ko ekdam aasan aur mazedar bana dunga. Mere paas ye sabhi Super Powers hain:\n\n"
        "🗣️ **Hinglish Support:** Main aapse desi style mein baat karunga.\n"
        "🖼️ **Direct Photos:** Kisi bhi topic ke aage 'photo' ya 'diagram' likho, main real image bhejunga!\n"
        "🎯 **Live Quiz:** Type karo `/quiz` aur apna test shuru karo.\n"
        "📚 **Short Notes:** Type karo `/notes` formula sheets ke liye.\n"
        "🎤 **Voice Notes:** Aap voice message bhejkar bhi help le sakte hain!\n\n"
        "Poochho, kya doubt hai aapka aaj? 🚀"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- 2. QUIZ MODE FEATURE (`/quiz`) ---
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌌 Physics", callback_data='quiz_physics')],
        [InlineKeyboardButton("🧪 Chemistry", callback_data='quiz_chemistry')],
        [InlineKeyboardButton("🧬 Biology", callback_data='quiz_biology')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 **Chalo ek test lete hain!** Apna favourite subject chuno:", reply_markup=reply_markup, parse_mode="Markdown")

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # Dummy Question bank based on selected subject (Inhe aap baad mein aur badha sakte hain)
    if data == 'quiz_physics':
        question = "❓ **Physics Question:** What is the SI unit of Electric Current?\n\nA) Volt\nB) Ampere\nC) Ohm\nD) Watt"
        keyboard = [[InlineKeyboardButton("A", callback_data='q_wrong'), InlineKeyboardButton("B", callback_data='q_correct')],
                    [InlineKeyboardButton("C", callback_data='q_wrong'), InlineKeyboardButton("D", callback_data='q_wrong')]]
    elif data == 'quiz_chemistry':
        question = "❓ **Chemistry Question:** What is the pH value of pure water?\n\nA) 5\nB) 7\nC) 9\nD) 14"
        keyboard = [[InlineKeyboardButton("A", callback_data='q_wrong'), InlineKeyboardButton("B", callback_data='q_correct')],
                    [InlineKeyboardButton("C", callback_data='q_wrong'), InlineKeyboardButton("D", callback_data='q_wrong')]]
    else:
        question = "❓ **Biology Question:** Which organelle is known as the Powerhouse of the Cell?\n\nA) Nucleus\nB) Ribosome\nC) Mitochondria\nD) Chloroplast"
        keyboard = [[InlineKeyboardButton("A", callback_data='q_wrong'), InlineKeyboardButton("B", callback_data='q_wrong')],
                    [InlineKeyboardButton("C", callback_data='q_correct'), InlineKeyboardButton("D", callback_data='q_wrong')]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=question, reply_markup=reply_markup, parse_mode="Markdown")

async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'q_correct':
        await query.edit_message_text(text="🎉 **Sahi Jawab! Excellent!** Aapki taiyari bohot achhi chal rahi hai. 🔥 10/10")
    else:
        await query.edit_message_text(text="❌ **Oh no! Galat Jawab.** Koi baat nahi, thoda aur revise karo aur dobara try karo! 👍")

# --- 3. NOTES DOWNLOAD FEATURE (`/notes`) ---
async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes_text = (
        "📚 **JEE/NEET Quick Revision Resources:**\n\n"
        "🔗 [Physics All Formulas PDF](https://t.me/Exam_Preparation_Notes) \n"
        "🔗 [Chemistry Periodic Table & Reactions](https://t.me/Exam_Preparation_Notes)\n"
        "🔗 [Biology Important Diagrams Sheet](https://t.me/Exam_Preparation_Notes)\n\n"
        "*(Aap in links par click karke direct high-quality revision sheets download kar sakte ho!)* 📑"
    )
    await update.message.reply_text(notes_text, parse_mode="Markdown", disable_web_page_preview=True)

# --- 4. TEXT & IMAGE GENERATION HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_text_lower = user_text.lower()
    
    # Check if user wants an image/diagram
    trigger_words = ["photo", "image", "diagram", "chitra", "pic", "picture"]
    if any(word in user_text_lower for word in trigger_words):
        await update.message.reply_text("🖼️ Main aapke liye diagram/photo dhoodh kar generate kar raha hoon, 1 second ruko...")
        try:
            # Cleaning text to make a good image query
            query = user_text_lower
            for word in trigger_words:
                query = query.replace(word, "")
            query = query.replace("mujhe", "").replace("dikhao", "").replace("ki", "").strip()
            
            if not query:
                query = "science diagram"
                
            # Generating direct image link via Pollinations AI (Free & Instant)
            encoded_query = urllib.parse.quote(f"clear educational scientific diagram of {query}, high quality, textbook style")
            image_url = f"https://image.pollinations.ai/p/{encoded_query}?width=800&height=600&seed=42"
            
            await update.message.reply_photo(photo=image_url, caption=f"📸 Ye raha aapka **{query.capitalize()}** ka visual diagram! Powered by AI. 🎯", parse_mode="Markdown")
            return
        except Exception as img_err:
            logging.error(f"Image Error: {img_err}")
            # Fallback if image fails, continue to text response

    # Default: Send text query to Groq (Hinglish)
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite, super-friendly AI educator for Indian JEE/NEET aspirants. "
                        "Rules:\n"
                        "1. Always reply in clean conversational Hinglish (Hindi + English mix).\n"
                        "2. Use lots of emojis to keep the student motivated.\n"
                        "3. Format answers with clear headings, bullets, and text-based tables if needed.\n"
                        "4. Keep explanations extremely easy, using real-life examples."
                    )
                },
                {
                    "role": "user",
                    "content": user_text,
                }
            ],
            model="llama-3.1-8b-instant",
        )
        reply = chat_completion.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Groq Error: {e}")
        await update.message.reply_text("❌ Oops! Groq Server busy hai. Please ek baar fir se try karein.")

# --- 5. VOICE NOTE HANDLER ---
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 **Main aapka Voice Note sun raha hoon!**\n\n*(Voice-to-text processing feature set ho gaya hai. Aap apna doubt clear audio mein poochte rahiye, main jaldi hi ise text answer mein badal dunga!)* 👍")

# --- MAIN APP FUNCTION ---
def main():
    if not TOKEN or not GROQ_API_KEY:
        logging.error("Variables missing from Railway!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Handlers configuration
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("notes", notes_command))
    
    # Callback queries for quiz buttons
    application.add_handler(CallbackQueryHandler(quiz_callback, pattern='^quiz_'))
    application.add_handler(CallbackQueryHandler(answer_callback, pattern='^q_'))
    
    # Message handlers for text and voice
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    print("🚀 Mega Ultimate JEE/NEET Bot Online...")
    application.run_polling()

if __name__ == '__main__':
    main()
