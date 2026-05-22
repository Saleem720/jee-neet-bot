import os
import telebot
from groq import Groq

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 🚀 WELCOME MESSAGE
# ==========================================
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "🎓 **Welcome to Tutorbhai Bot!**\n\n"
        "Main aapki padhai asaan banane ke liye tayaar hoon.\n"
        "🎙️ **Voice/Audio Bhejo:** Apne lecture ko short notes me badalne ke liye!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

# ==========================================
# 🎙️ VOICE HANDLER WITH SYSTEM FFMPEG
# ==========================================
@bot.message_handler(content_types=['voice', 'audio'])
def handle_student_voice(message):
    bot.reply_to(message, "⏳ Aapki voice note mil gayi hai! Tutorbhai AI isko short notes me badal raha hai...")
    
    file_name = f"voice_{message.chat.id}.ogg"
    
    try:
        # 1. Telegram se file download karo
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 2. Local disk par temporarily save karo
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # 3. Groq API Call (Ab ffmpeg hone ki wajah se direct file utha lega)
        with open(file_name, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text"
            )

        if not transcription or str(transcription).strip() == "":
            bot.reply_to(message, "❌ Audio clear nahi tha. Dobara bhejein.")
            return

        # 4. Llama-3 AI Notes Generation
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": "Aap Tutorbhai Bot ke ek helpful AI assistant hain. Diye gaye text se clean Hinglish/English mix short notes banayein."},
                {"role": "user", "content": str(transcription)}
            ]
        )

        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{completion.choices[0].message.content}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me dikkat aayi.")
        print(f"Error: {e}")
        
    finally:
        # Cleanup file
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == '__main__':
    bot.polling(none_stop=True)
