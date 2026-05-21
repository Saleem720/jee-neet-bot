import os
import logging
import anthropic
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================================
# CONFIGURATION - Railway environment variables se aayega
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY")

# ============================================================
# Logging setup
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# Anthropic client
# ============================================================
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Memory: har user ki chat history store karne ke liye
user_histories: dict[int, list[dict]] = {}

# ============================================================
# /start command
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Assalam-o-Alaikum {user.first_name}! 👋\n\n"
        "Main aapka JEE/NEET AI Assistant hoon!\n\n"
        "✅ Physics, Chemistry, Math, Biology ke doubts\n"
        "✅ Step-by-step solutions\n"
        "✅ Practice questions\n"
        "✅ 24/7 available\n\n"
        "Apna doubt likhiye! 📚\n"
        "Type /clear to reset conversation."
    )

# ============================================================
# /clear command
# ============================================================
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ Conversation reset ho gayi!")

# ============================================================
# Normal message handler
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id   = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_text})

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="""Tu ek expert JEE aur NEET AI tutor hai.

Tujhe in subjects mein expertise hai:
- JEE: Physics, Chemistry, Mathematics
- NEET: Physics, Chemistry, Biology

Kaise jawab de:
1. Pehle concept clearly explain kar
2. Step-by-step solution de
3. Formula highlight kar
4. Agar ho sake toh ek example de
5. Hinglish mein baat kar (Hindi + English mix)
6. Encouraging rehna — student ka confidence badhana hai

Agar student galat samjhe toh gently correct kar.""",
            messages=user_histories[user_id],
        )

        reply_text = response.content[0].text
        user_histories[user_id].append({"role": "assistant", "content": reply_text})

        if len(reply_text) > 4096:
            for i in range(0, len(reply_text), 4096):
                await update.message.reply_text(reply_text[i : i + 4096])
        else:
            await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Kuch error aayi. Thodi der baad try karein.")

# ============================================================
# Main
# ============================================================
def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("JEE/NEET Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
