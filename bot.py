import os
import io
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from groq import Groq

# ==========================================
# ⚙️ CONFIGURATION (DIRECT RAILWAY MATCH)
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
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
        "🎙️ **Voice/Audio Bhejo:** Apne lecture ko short notes me badalne ke liye!"
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

    try:
        # 1. File ID extract karo aur content type check karo
        if message.voice:
            file_id = message.voice.file_id
            # Groq API stream pipelines ke liye strict standard file name dena safe hota hai
            filename = "sample.opus" 
        else:
            file_id = message.audio.file_id
            orig_name = getattr(message.audio, 'file_name', '')
            ext = os.path.splitext(orig_name)[1].lower() if orig_name else '.mp3'
            filename = f"sample{ext}"

        # 2. Telegram Server se direct direct byte data fetch karo
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        response = requests.get(file_url)
        if response.status_code != 200:
            raise Exception("Telegram content fetch failed.")
            
        audio_content = response.content

        # 3. File object ko memory wrapper (io.BytesIO) me wrap karke standard stream model banana
        audio_file_like = io.BytesIO(audio_content)
        audio_file_like.name = filename  # Groq requirements ke liye meta-name inject karna compulsory hai

        # 4. Groq Whisper transcription call
        transcription_data = groq_client.audio.transcriptions.create(
            file=audio_file_like,
            model="whisper-large-v3",
            response_format="json"
        )

        # Response extract karna
        transcription_text = transcription_data.text if hasattr(transcription_data, 'text') else str(transcription_data)

        if not transcription_text or transcription_text.strip() == "":
            bot.reply_to(message, "❌ Is audio me mujhe koi clear aawaz sunai nahi di. Kripya thoda saaf aur lamba audio record karke bhejein.")
            return

        # 5. Llama-3 AI se smart quality notes banana
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {
                    "role": "system", 
                    "content": "Aap Tutorbhai Bot ke ek helpful AI assistant hain. Diye gaye educational lecture ke audio text mese important bullet points, key definitions aur summary nikal kar ekdum clean, easy-to-understand Hinglish/English mix notes taiyar karein."
                },
                {
                    "role": "user", 
                    "content": transcription_text
                }
            ]
        )

        ai_notes = completion.choices[0].message.content
        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{ai_notes}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me thodi dikkat aayi. Kripya ek baar dobara koshish karein.")
        print(f"Server Core Log: {e}")


# ==========================================
# 🏁 BOT START POLLING
# ==========================================
if __name__ == '__main__':
    print("Tutorbhai Bot is running successfully...")
    bot.polling(none_stop=True)
