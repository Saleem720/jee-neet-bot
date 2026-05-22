import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# ⚙️ CONFIGURATION (DIRECT RAILWAY MATCH)
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🚀 WELCOME INTERFACE WITH MENUS ONLY
# ==========================================
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
    
    markup.add(btn_physics, btn_chemistry)
    markup.add(btn_biology, btn_maths)
    markup.add(btn_quiz, btn_diagram)
    markup.row(btn_notes)
    
    welcome_text = (
        "🎓 **Welcome to Tutorbhai Bot!**\n\n"
        "Main aapki padhai ko asaan banane ke liye tayaar hoon. Study material aur modules ke liye neeche diye gaye buttons ka upyog karein!"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')


# ==========================================
# 🎛️ BUTTONS CLICK HANDLER (ONLY FIXED TEXT REPLIES)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == 'notes_feature':
        bot.send_message(
            call.message.chat.id, 
            "📚 **Tutorbhai Notes:**\nSyllabus ke anusar important chapters aur notes jald hi yahan upload kiye jayenge. Jude rahein!",
            parse_mode='Markdown'
        )
    elif call.data.startswith('subject_'):
        subject_name = call.data.split('_')[1].capitalize()
        bot.send_message(
            call.message.chat.id, 
            f"📖 **{subject_name} Module:**\nIs subject ke standard questions aur reference material jald hi chalu honge.", 
            parse_mode='Markdown'
        )
    elif call.data == 'feature_quiz':
        bot.send_message(
            call.message.chat.id, 
            "🎯 **Quiz Mode:**\nMock tests aur quick daily quizzes ka feature jald hi chalu kiya jayega!"
        )
    elif call.data == 'feature_diagram':
        bot.send_message(
            call.message.chat.id, 
            "🖼️ **Diagram Mode:**\nImportant educational diagrams aur charts ka access aapko jald hi is button par milega."
        )
    
    bot.answer_callback_query(call.id)


# ==========================================
# 🏁 BOT START POLLING (ALL PHOTO/TEXT EXTRA HANDLERS DETACHED)
# ==========================================
if __name__ == '__main__':
    print("Tutorbhai Engine successfully running on pure button interface mode...")
    bot.polling(none_stop=True, timeout=60)
