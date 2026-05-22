import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
# Groq client initialize karte waqt check karenge ki key hai ya nahi
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
else:
    print("WARNING: GROQ_API_KEY missing!")

@bot.message_handler(commands=['start'])
def welcome(message):
    # Buttons UI
    markup = InlineKeyboardMarkup(row_width=2)
    # ... (buttons waise hi rahenge)
    markup.add(InlineKeyboardButton("⚛️ Physics", callback_data="subject_physics"),
               InlineKeyboardButton("🧪 Chemistry", callback_data="subject_chemistry"))
    bot.send_message(message.chat.id, "🎓 **Welcome to Hire Orbit!**\n\nMain aapka AI Tutor hoon. Apna sawaal poochiye!", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if not GROQ_API_KEY:
        bot.reply_to(message, "Error: Bot ki API key configure nahi hai.")
        return
        
    try:
        # LLM Call
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        # Error ko print karenge taaki logs mein dekh sakein
        print(f"DEBUG ERROR: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

bot.polling(none_stop=True)
