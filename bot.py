import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq

# Configuration
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = InlineKeyboardMarkup(row_width=2)
    # Buttons logic...
    markup.add(InlineKeyboardButton("⚛️ Physics", callback_data="subject_physics"),
               InlineKeyboardButton("🧪 Chemistry", callback_data="subject_chemistry"))
    bot.send_message(message.chat.id, "🎓 **Welcome to Hire Orbit!**\n\nMain aapka AI Tutor hoon. Apna sawaal poochiye!", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        # MODEL UPDATED HERE: llama3-8b-8192 -> llama-3.3-70b-versatile
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Aap ek expert tutor hain. Chote aur saaf jawab dein."},
                      {"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
