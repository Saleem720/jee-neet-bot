import os
import logging
import urllib.parse
import json
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from groq import Groq

# Logging set up
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

# --- 1. START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Hello Dost! Main hoon Padaiwala Dost (V2.0 Advance)!** 🔥\n\n"
        "Ab main pehle se zyada smart aur advanced ho gaya hoon. Dekho ab main kya-kya kar sakta hoon:\n\n"
        "🧠 **AI Dynamic Quiz:** `/quiz` type karo, aur main Groq AI se live naye JEE/NEET MCQs generate karunga.\n"
        "🖼️ **Instant HD Diagrams:** Kuch bhi padhte waqt 'photo' ya 'diagram' maango, instant visual hazir.\n"
        "⚡ **JEE/NEET Hacks:** Main aapko shortcuts, formulas aur step-by-step derivations bhi samjhaunga.\n\n"
        "Chalo, taiyari shuru karein? Koi bhi sawaal pucho ya `/quiz` se test lo! 🚀"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- 2. ADVANCED AI-POWERED QUIZ GENERATOR ---
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌌 Physics", callback_data='subj_physics')],
        [InlineKeyboardButton("🧪 Chemistry", callback_data='subj_chemistry')],
        [InlineKeyboardButton("🧬 Biology", callback_data='subj_biology')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 **Let's generate a Live AI Quiz!** Apna subject chuno:", reply_markup=reply_markup, parse_mode="Markdown")

async def subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject = query.data.split('_')[1]
    
    await query.edit_message_text(text=f"🔄 **Groq AI se fresh JEE/NEET {subject.capitalize()} ka question generate ho raha hai...** Ek second ruko.")

    try:
        # Groq AI se strict JSON format mein question mangna
        prompt = (
            f"Generate one high-quality multiple-choice question (MCQ) for JEE/NEET level {subject}. "
            "Provide the response strictly in JSON format with keys: 'question', 'A', 'B', 'C', 'D', 'correct_option', 'explanation'. "
            "Keep the language of explanation in conversational Hinglish, but the question and options in technical English. "
            "Ensure the correct_option is exactly one letter: 'A', 'B', 'C', or 'D'."
        )
        
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        quiz_data = json.loads(completion.choices[0].message.content)
        
        # Format the question output
        formatted_question = (
            f"🎯 **JEE/NEET {subject.capitalize()} Challenge!**\n\n"
            f"❓ {quiz_data['question']}\n\n"
            f"🅰️ {quiz_data['A']}\n"
            f"🅱️ {quiz_data['B']}\n"
            f"🆃 {quiz_data['C']}\n"
            f"🅳 {quiz_data['D']}\n"
        )
        
        # Save exact details in user_data for evaluation later
        context.user_data['correct'] = quiz_data['correct_option'].strip().upper()
        context.user_data['explanation'] = quiz_data['explanation']
        
        keyboard = [
            [InlineKeyboardButton("A", callback_data='ans_A'), InlineKeyboardButton("B", callback_data='ans_B')],
            [InlineKeyboardButton("C", callback_data='ans_C'), InlineKeyboardButton("D", callback_data='ans_D')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=formatted_question, reply_markup=reply_markup, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Quiz Gen Error: {e}")
        await query.edit_message_text(text="❌ Sawaal banane mein thodi dikkat aayi. Ek baar fir se `/quiz` try karo bro!")

async def check_answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_ans = query.data.split('_')[1]
    correct_ans = context.user_data.get('correct', 'A')
    explanation = context.user_data.get('explanation', 'Koi explanation available nahi hai.')
    
    if user_ans == correct_ans:
        result_text = f"🎉 **💥 SAHI JAWAB! Brilliant!** Your choice ({user_ans}) is absolutely correct.\n\n"
    else:
        result_text = f"❌ **OH NO! Galat Jawab.** Sahi option **{correct_ans}** tha.\n\n"
        
    result_text += f"💡 **Detailed Explanation (Hinglish):**\n{explanation}\n\n👉 Naya sawaal chahiye? Type karo `/quiz`!"
    
    await query.edit_message_text(text=result_text, parse_mode="Markdown")

# --- 3. NOTES DOWNLOAD FEATURE (`/notes`) ---
async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    notes_text = (
        "📚 **JEE/NEET Ultimate Revision Sheets:**\n\n"
        "🔹 [Physics Formulas Cheat-Sheet](https://t.me/Exam_Preparation_Notes)\n"
        "🔹 [Chemistry Organic Name Reactions](https://t.me/Exam_Preparation_Notes)\n"
        "🔹 [Biology High-Yield Diagrams Guide](https://t.me/Exam_Preparation_Notes)\n\n"
        "💡 *Tip: Revision sheets ko bookmarks mein save kar lo short-term studies ke liye!*"
    )
    await update.message.reply_text(notes_text, parse_mode="Markdown", disable_web_page_preview=True)

# --- 4. ADVANCED TEXT & IMAGE HANDLER ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_text_lower = user_text.lower()
    
    trigger_words = ["photo", "image", "diagram", "chitra", "pic", "picture", "map"]
    if any(word in user_text_lower for word in trigger_words):
        await update.message.reply_text("🖼️ Main aapke liye textbook-style diagram create kar raha hoon, thoda sabr rakho...")
        try:
            query = user_text_lower
            for word in trigger_words:
                query = query.replace(word, "")
            query = query.replace("mujhe", "").replace("dikhao", "").replace("ki", "").strip()
            
            if not query:
                query = "science concept"
                
            # Better prompt engineering for generating standard educational diagrams
            encoded_query = urllib.parse.quote(f"clear detailed educational scientific labeled diagram of {query}, white background, crisp textbook illustration")
            image_url = f"https://image.pollinations.ai/p/{encoded_query}?width=900&height=700&seed=100"
            
            await update.message.reply_photo(photo=image_url, caption=f"📸 **Here is your diagram for: {query.capitalize()}**\n\nPadhai ke liye best and clean layout structure. 🎯", parse_mode="Markdown")
            return
        except Exception as img_err:
            logging.error(f"Image Gen Error: {img_err}")

    # Text completion handling (Advanced Hinglish Teacher Context)
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite, highly interactive JEE/NEET personal mentor named 'Padaiwala Dost'. "
                        "Rules:\n"
                        "1. Talk in friendly, enthusiastic Hinglish.\n"
                        "2. Always simplify tough equations/concepts by using analogies, breakdowns, and points.\n"
                        "3. Highlight critical formulas using markdown text code format so they stand out.\n"
                        "4. End your response with a motivational one-liner or an engaging question related to the topic."
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
        await update.message.reply_text("❌ Server thoda busy ho gaya, please ek baar fir se try karo!")

# --- 5. VOICE NOTE COMPATIBILITY ---
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 **Aapka voice command received!** Main jaldi hi is audio feature ko backend transcribing se direct link kar dunga. Tab tak ke liye ek baar question type karke dekho dost! 👍")

# --- MAIN CONTROLLER ---
def main():
    if not TOKEN or not GROQ_API_KEY:
        logging.error("Credentials missing!")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))
    application.add_handler(CommandHandler("notes", notes_command))
    
    # Callback queries routers
    application.add_handler(CallbackQueryHandler(subject_callback, pattern='^subj_'))
    application.add_handler(CallbackQueryHandler(check_answer_callback, pattern='^ans_'))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    
    print("🚀 Padaiwala Dost V2.0 Successfully Running...")
    application.run_polling()

if __name__ == '__main__':
    main()
