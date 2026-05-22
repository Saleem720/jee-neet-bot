import os
import logging
import json
import base64
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from groq import Groq
import anthropic

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ─── CREDENTIALS ──────────────────────────────────────────────────────────────
TOKEN          = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")   # NEW: Claude for image analysis

groq_client    = Groq(api_key=GROQ_API_KEY)
claude_client  = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Tu "Padaiwala Dost" hai — ek expert aur friendly JEE/NEET study mentor.

## Tera style:
- Hinglish mein baat kar (Hindi + English mix) — jaise ek dost bolta hai
- Encouraging tone — "beta", "yaar", "bilkul sahi" use karo
- Complex concepts ko simple analogies se samjhao

## Har response mein:
1. Concept ka naam **bold** mein
2. Simple explanation (2-3 lines Hinglish)
3. **Key Formula** (if applicable) — clearly formatted using backticks
4. **Trick/Mnemonic** — easy yaad karne ke liye
5. Ek motivating line ya engaging follow-up question

## Rules:
- Always Hinglish mein jawab do
- Formulas ko `code format` mein likho taaki clearly dikhein
- Kabhi galat info mat do — agar pata nahi toh bol do
- Response concise rakho — max 300 words
"""

# ─── USER SESSION STORAGE ─────────────────────────────────────────────────────
# { user_id: { exam, class_level, onboarded, history: [...] } }
user_sessions: dict[int, dict] = {}

def get_session(user_id: int) -> dict:
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "exam":        None,
            "class_level": None,
            "onboarded":   False,
            "history":     [],   # Groq message history
        }
    return user_sessions[user_id]

# ─── GROQ CHAT HELPER (with conversation memory) ──────────────────────────────
def ask_groq(session: dict, user_text: str) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add student context to very first user message
    history = session["history"]
    if not history:
        context_line = (
            f"[Student info — Exam: {session.get('exam','JEE/NEET')}, "
            f"Class: {session.get('class_level','12')}]\n\n"
        )
        user_text = context_line + user_text

    messages += history[-10:]   # last 5 turns (10 messages) — token safe
    messages.append({"role": "user", "content": user_text})

    response = groq_client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",   # UPGRADED: much smarter model
        temperature=0.6,
        max_tokens=700,
    )
    reply = response.choices[0].message.content

    # Save to history
    session["history"].append({"role": "user",      "content": user_text})
    session["history"].append({"role": "assistant",  "content": reply})

    return reply

# ─── CLAUDE IMAGE ANALYSIS ────────────────────────────────────────────────────
def analyze_image_claude(image_bytes: bytes, caption: str = "") -> str:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    prompt = caption if caption else "Is diagram ko explain karo."

    response = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text",  "text": (
                    f"{prompt}\n\n"
                    "Yeh karo:\n"
                    "1. Diagram ka naam batao\n"
                    "2. Kya show ho raha hai samjhao (Hinglish mein)\n"
                    "3. Related important formulas likho\n"
                    "4. JEE/NEET mein kaise poochha jata hai batao"
                )},
            ],
        }],
    )
    return response.content[0].text

# ─── KEYBOARDS ────────────────────────────────────────────────────────────────
def exam_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🏥 NEET",        callback_data="exam_NEET"),
        InlineKeyboardButton("🔬 JEE",         callback_data="exam_JEE"),
        InlineKeyboardButton("📚 Board Only",  callback_data="exam_Board"),
    ]])

def class_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Class 11", callback_data="class_11"),
        InlineKeyboardButton("Class 12", callback_data="class_12"),
        InlineKeyboardButton("Dono",     callback_data="class_both"),
    ]])

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚛️ Physics",    callback_data="subj_physics"),
            InlineKeyboardButton("🧪 Chemistry",  callback_data="subj_chemistry"),
        ],
        [
            InlineKeyboardButton("🧬 Biology",    callback_data="subj_biology"),
            InlineKeyboardButton("📐 Maths",      callback_data="subj_maths"),
        ],
        [
            InlineKeyboardButton("🎯 Quiz",       callback_data="quick_quiz"),
            InlineKeyboardButton("📚 Notes",      callback_data="quick_notes"),
        ],
    ])

def quiz_subject_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌌 Physics",   callback_data='subj_physics')],
        [InlineKeyboardButton("🧪 Chemistry", callback_data='subj_chemistry')],
        [InlineKeyboardButton("🧬 Biology",   callback_data='subj_biology')],
        [InlineKeyboardButton("📐 Maths",     callback_data='subj_maths')],   # NEW
    ])

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session(user.id)
    session["onboarded"] = False
    session["history"]   = []

    await update.message.reply_text(
        f"👋 *Namaste {user.first_name} bhai/behen!*\n\n"
        "Main hoon *Padaiwala Dost V2.0* — tera AI study partner! 🚀\n\n"
        "Pehle bata — kaunsi exam ki taiyari kar raha/rahi hai?",
        parse_mode="Markdown",
        reply_markup=exam_keyboard(),
    )

# ─── CALLBACK HANDLER ─────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = get_session(user_id)
    data    = query.data

    # Exam selection
    if data.startswith("exam_"):
        session["exam"] = data.replace("exam_", "")
        await query.edit_message_text(
            f"✅ *{session['exam']}* — great choice!\n\nAb bata, kaunsi class mein hai?",
            
            reply_markup=class_keyboard(),
        )

    # Class selection
    elif data.startswith("class_"):
        session["class_level"] = data.replace("class_", "")
        session["onboarded"]   = True
        await query.edit_message_text(
            f"🎯 *{session['exam']}* + *Class {session['class_level']}* — perfect!\n\n"
            "Ab koi bhi topic type karo, ya neeche se choose karo 👇",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )

    # Subject shortcut → ask topic
    elif data.startswith("subj_") and not context.user_data.get("quiz_mode"):
        subject = data.replace("subj_", "").capitalize()
        await query.message.reply_text(
            f"📚 *{subject}* — kaunsa topic? Type karo! (e.g., Newton's Laws, Organic Chemistry)",
            parse_mode="Markdown",
        )

    # Quick quiz from main menu
    elif data == "quick_quiz":
        await query.message.reply_text(
            "🎯 *Live AI Quiz!* Subject chuno:",
            parse_mode="Markdown",
            reply_markup=quiz_subject_keyboard(),
        )
        context.user_data["quiz_mode"] = True

    # Subject selected for QUIZ
    elif data.startswith("subj_") and context.user_data.get("quiz_mode"):
        context.user_data["quiz_mode"] = False
        subject = data.split('_')[1]
        await _generate_quiz(query, context, subject)

    # Quiz answer
    elif data.startswith("ans_"):
        user_ans    = data.split('_')[1]
        correct_ans = context.user_data.get('correct', 'A')
        explanation = context.user_data.get('explanation', 'Explanation available nahi hai.')

        if user_ans == correct_ans:
            result = f"🎉 *SAHI JAWAB!* ({user_ans}) Bilkul correct! 💥\n\n"
        else:
            result = f"❌ *Galat!* Sahi answer tha *{correct_ans}*.\n\n"

        result += f"💡 *Explanation:*\n{explanation}\n\n👉 Naya sawaal? /quiz"
        await query.edit_message_text(result, parse_mode="Markdown")

    # Quick notes
    elif data == "quick_notes":
        await _send_notes(query.message)

# ─── QUIZ GENERATOR ───────────────────────────────────────────────────────────
async def _generate_quiz(query, context, subject: str):
    await query.edit_message_text(
        f"🔄 *Groq AI se fresh {subject.capitalize()} question ban raha hai...* Ek second! ⏳",
        parse_mode="Markdown",
    )
    try:
        prompt = (
            f"Generate one high-quality MCQ for JEE/NEET level {subject}. "
            "Respond ONLY in JSON with keys: question, A, B, C, D, correct_option, explanation. "
            "Explanation in Hinglish. correct_option must be exactly A, B, C, or D."
        )
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        qd = json.loads(completion.choices[0].message.content)

        text = (
            f"🎯 *JEE/NEET {subject.capitalize()} Challenge!*\n\n"
            f"❓ {qd['question']}\n\n"
            f"🅰️ {qd['A']}\n"
            f"🅱️ {qd['B']}\n"
            f"🆃 {qd['C']}\n"
            f"🅳 {qd['D']}\n"
        )
        context.user_data['correct']     = qd['correct_option'].strip().upper()
        context.user_data['explanation'] = qd['explanation']

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("A", callback_data='ans_A'), InlineKeyboardButton("B", callback_data='ans_B')],
            [InlineKeyboardButton("C", callback_data='ans_C'), InlineKeyboardButton("D", callback_data='ans_D')],
        ])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Quiz error: {e}")
        await query.edit_message_text("❌ Sawaal banane mein dikkat aayi. /quiz se fir try karo!")

# ─── /quiz COMMAND ────────────────────────────────────────────────────────────
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["quiz_mode"] = True
    await update.message.reply_text(
        "🎯 *Live AI Quiz!* Subject chuno:",
        parse_mode="Markdown",
        reply_markup=quiz_subject_keyboard(),
    )

# ─── /notes COMMAND ───────────────────────────────────────────────────────────
async def _send_notes(message):
    await message.reply_text(
        "📚 *JEE/NEET Revision Sheets:*\n\n"
        "🔹 [Physics Formulas Cheat-Sheet](https://t.me/Exam_Preparation_Notes)\n"
        "🔹 [Chemistry Organic Name Reactions](https://t.me/Exam_Preparation_Notes)\n"
        "🔹 [Biology High-Yield Diagrams Guide](https://t.me/Exam_Preparation_Notes)\n\n"
        "💡 *Tip: Bookmarks mein save karo quick revision ke liye!*",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_notes(update.message)

# ─── TEXT HANDLER ─────────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    session  = get_session(user_id)
    user_text = update.message.text

    # Not onboarded yet
    if not session["onboarded"]:
        await update.message.reply_text(
            "Pehle /start karke apna setup complete karo! 😊"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = ask_groq(session, user_text)
        await update.message.reply_text(
            reply,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logging.error(f"Groq error: {e}")
        await update.message.reply_text("❌ Server busy hai, ek baar fir try karo!")

# ─── IMAGE HANDLER (NEW — Claude powered) ────────────────────────────────────
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = get_session(user_id)

    if not session["onboarded"]:
        await update.message.reply_text("Pehle /start karke setup complete karo! 😊")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    await update.message.reply_text("🖼️ Diagram dekh raha hoon... ek second! 🔍")

    try:
        photo    = update.message.photo[-1]
        file     = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        caption  = update.message.caption or ""

        reply = analyze_image_claude(bytes(img_bytes), caption)
        await update.message.reply_text(
            reply,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
    except Exception as e:
        logging.error(f"Image error: {e}")
        await update.message.reply_text("❌ Image analyse nahi ho paayi. Dobara bhejo!")

# ─── VOICE HANDLER ────────────────────────────────────────────────────────────
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎤 Voice feature coming soon! Abhi ke liye question *type* karke bhejo dost. 👍",
        parse_mode="Markdown",
    )

# ─── /menu COMMAND ────────────────────────────────────────────────────────────
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Kya padhna hai aaj? 👇",
        reply_markup=main_menu_keyboard(),
    )

# ─── /reset COMMAND ───────────────────────────────────────────────────────────
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "🔁 Session reset! /start se naye sire se shuru karo."
    )

# ─── /help COMMAND ────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Padaiwala Dost V2.0 — Help*\n\n"
        "Main kya kar sakta hoon:\n"
        "• Koi bhi *Physics, Chemistry, Bio, Maths* topic explain karna\n"
        "• *Diagram/Photo* bhejo → Claude AI se detailed explanation\n"
        "• *Live AI Quiz* — fresh JEE/NEET MCQs\n"
        "• *Conversation yaad rakhta hoon* — baar baar explain nahi karna\n\n"
        "Commands:\n"
        "/start — Setup shuru karo\n"
        "/quiz  — Live AI quiz\n"
        "/notes — Revision sheets\n"
        "/menu  — Main menu\n"
        "/reset — Session reset\n"
        "/help  — Yeh message",
        parse_mode="Markdown",
    )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not TOKEN or not GROQ_API_KEY:
        logging.error("TELEGRAM_BOT_TOKEN ya GROQ_API_KEY missing!")
        return
    if not ANTHROPIC_KEY:
        logging.warning("ANTHROPIC_API_KEY missing — image analysis kaam nahi karega!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("quiz",   quiz_command))
    app.add_handler(CommandHandler("notes",  notes_command))
    app.add_handler(CommandHandler("menu",   menu_command))
    app.add_handler(CommandHandler("reset",  reset_command))
    app.add_handler(CommandHandler("help",   help_command))

    # Callback queries
    app.add_handler(CallbackQueryHandler(button_handler, pattern='^(exam_|class_|subj_|ans_|quick_)'))

    # Message handlers
    app.add_handler(MessageHandler(filters.PHOTO,              handle_image))
    app.add_handler(MessageHandler(filters.VOICE,              handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Padaiwala Dost V2.0 chal raha hai...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
