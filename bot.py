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
    markup.add(InlineKeyboardButton("⚛️ Physics", callback_data="subject_physics"),
               InlineKeyboardButton("🧪 Chemistry", callback_data="subject_chemistry"))
    bot.send_message(message.chat.id, "🎓 **Welcome to Hire Orbit!**\n\nMain aapka JEE/NEET Expert AI Tutor hoon. Apna sawaal poochiye, main diagrams aur examples se samjhaunga!", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        # JEE/NEET Expert System Prompt
        system_instruction = (
            "Aap ek top-tier JEE/NEET Expert AI Tutor hain. "
            "1. Jawab hamesha Hinglish mein dein. "
            "2. Complex concepts ko emojis aur bullet points ka use karke simplify karein. "
            "3. Diagram related concepts ke liye steps clear likhein (jaise: 'Step 1: X draw karo'). "
            "4. Student ko motivate karein aur jawab ke end mein ek related practice question zaroor poochain."
        )
        
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": message.text}
            ]
        )
        bot.reply_to(message, completion.choices[0].message.content, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

if __name__ == '__main__':
    bot.polling(none_stop=True)
