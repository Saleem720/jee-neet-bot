import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq

# ==========================================
# ⚙️ COFIGURATION (RAILWAY VARIABLES SE)
# ==========================================
# Yeh automatic aapke Railway Config Vars se keys utha lega
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Agar Railway me naam alag hai, toh wo naam yahan likhein
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Initialize Bot and AI Client
bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)


# ==========================================
# 🚀 WELCOME MESSAGE & MAIN INTERFACE
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
        "Main aapki padhai asaan banane ke liye tayaar hoon. Niche diye gaye buttons use karein ya:\n"
        "📸 **Photo Bhejo:** Kisi bhi diagram ya sawaal ka solution paane ke liye.\n"
        "🎙️ **Voice/Audio Bhejo:** Apne lecture ko 5-second me short notes me badalne ke liye!"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')


# ==========================================
# 🎛️ BUTTONS CLICK HANDLER (CALLBACKS)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == 'notes_feature':
        bot.send_message(
            call.message.chat.id, 
            "🎙️ **Tutorbhai Voice Notes:**\nApne lecture ka audio file (.mp3, .m4a, .ogg) ya direct ek voice note yahan send karein. Main turant uske short notes bana dunga!",
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
# 🎙️ VOICE & AUDIO MESSAGE HANDLER
# ==========================================
@bot.message_handler(content_types=['voice', 'audio'])
def handle_student_voice(message):
    bot.reply_to(message, "⏳ Aapki voice note mil gayi hai! Tutorbhai AI isko short notes me badal raha hai...")

    file_name = f"voice_{message.chat.id}.ogg"
    try:
        file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        with open(file_name, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(file_name, audio_file.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {
                    "role": "system", 
                    "content": "Aap Tutorbhai Bot ke AI assistant hain. Diye gaye educational lecture ke audio text mese important bullet points, key definitions aur summary nikal kar ekdum clean Hinglish/English mix notes taiyar karein."
                },
                {
                    "role": "user", 
                    "content": transcription
                }
            ]
        )

        ai_notes = completion.choices[0].message.content
        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{ai_notes}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me thodi dikkat aayi. Kripya dobara koshish karein.")
        print(f"Error: {e}")
        
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)


# ==========================================
# 🏁 BOT START POLLING
# ==========================================
if __name__ == '__main__':
    print("Tutorbhai Bot is running successfully...")
    bot.polling(none_stop=True)
