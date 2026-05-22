import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# ⚙️ CONFIGURATION (DIRECT RAILWAY MATCH)
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 🚀 WELCOME MESSAGE & MAIN INTERFACE ONLY
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
        "Main aapki padhai asaan banane ke liye tayaar hoon. Niche diye gaye buttons use karein!"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')


# ==========================================
# 🎛️ BUTTONS CLICK HANDLER (ONLY FIXED REPLIES)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == 'notes_feature':
        bot.send_message(
            call.message.chat.id, 
            "📚 **Tutorbhai Notes:**\nApne topic ka naam text mein likh kar bhejiye, main aapko important notes de dunga!",
            parse_mode='Markdown'
        )
    elif call.data.startswith('subject_'):
        subject_name = call.data.split('_')[1].capitalize()
        bot.send_message(call.message.chat.id, f"Beta, ab tum **{subject_name}** ka agla sawaal try karo! 📖", parse_mode='Markdown')
    elif call.data == 'feature_quiz':
        bot.send_message(call.message.chat.id, "🎯 **Quiz Mode Chalu!** Main tumse jald hi sawaal poochunga.")
    elif call.data == 'feature_diagram':
        bot.send_message(call.message.chat.id, "🖼️ **Diagram Mode:** Mujhe koi bhi educational diagram ya map ki photo bhejo!")
    
    bot.answer_callback_query(call.id)


# ==========================================
# 🏁 BOT START POLLING (NO PHOTO/TEXT HANDLERS)
# ==========================================
if __name__ == '__main__':
    print("Tutorbhai Bot is running with ONLY button interfaces...")
    bot.polling(none_stop=True, timeout=60)
