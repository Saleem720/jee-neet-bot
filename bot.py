import os
import logging
from groq import Groq
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)
user_histories = {}

SYSTEM_PROMPT = """Tu ek expert JEE aur NEET AI tutor hai. Physics, Chemistry, Math, Biology mein expert hai. Step-by-step solution de, Hinglish mein baat kar, encouraging reh."""

async def start(update, context):
    await update.message.reply_text("Assalam-o-Alaikum! 👋\nMain aapka JEE/NEET AI Assistant hoon!\n✅ Physics, Chemistry, Math, Biology\n✅ 24/7 available\nApna doubt likhiye! 📚")

async def clear(update, context):
    user_histories[update.effective_user.id] = []
    await update.message.reply_text("✅ Reset ho gayi!")

async def handle_message(update, context):
    user_id = update.effective_user.id
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": update.message.text})
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + user_histories[user_id],
            max_tokens=1024,
        )
        reply = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error aayi, dobara try karein.")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot chal raha hai!")
    app.run_polling()

if __name__ == "__main__":
    main()
