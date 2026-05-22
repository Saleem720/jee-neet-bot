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
    btn_physics = InlineKeyboardButton("⚛️ Physics", callback_data="subject_physics")
    btn_chemistry = InlineKeyboardButton("🧪 Chemistry", callback_data="subject_chemistry")
    btn_biology = InlineKeyboardButton("🧬 Biology", callback_data="subject_biology")
    btn_maths = InlineKeyboardButton("📐 Maths", callback_data="subject_maths")
    btn_quiz = InlineKeyboardButton("🎯 Quiz", callback_data="feature_quiz")
    btn_diagram = InlineKeyboardButton("🖼️ Diagram", callback_data="feature_diagram")
    btn_notes = InlineKeyboardButton("📚 Notes", callback_data="notes_feature")
    markup.add(btn_physics, btn_chemistry, btn_biology, btn_maths, btn_quiz, btn_diagram)
    markup.row(btn_notes)
    
    bot.send_message(message.chat.id, "🎓 **Welcome to Hire Orbit Bot!**\n\nKuch bhi poochiye, main aapki padhai mein madad karunga!", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith('subject_'):
        bot.send_message(call.message.chat.id, f"📖 **{call.data.split('_')[1].capitalize()} Module:**\nMain is topic par research kar raha hoon, aap apna sawaal likh kar bhejiye!")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    # Llama-3 AI Engine for text answers
    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "system", "content": "Aap ek expert tutor hain. Chote aur saaf jawab dein."},
                      {"role": "user", "content": message.text}]
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Abhi server busy hai, thodi der mein try karein.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
