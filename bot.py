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
# 🚀 WELCOME INTERFACE
# ==========================================
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "🎓 **Welcome to Tutorbhai Bot!**\n\n"
        "Main aapki padhai asaan banane ke liye tayaar hoon.\n"
        "🎙️ **Voice Note ya Audio File Bhejo:** Main turant uske dhasu short notes bana dunga!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

# ==========================================
# 🎙️ AUDIO & VOICE HANDLER
# ==========================================
@bot.message_handler(content_types=['voice', 'audio'])
def handle_student_voice(message):
    bot.reply_to(message, "⏳ Aapki voice note mil gayi hai! Tutorbhai AI isko short notes me badal raha hai...")
    
    file_name = None
    
    try:
        # 1. File Type check karo aur safe extension name do
        if message.voice:
            file_id = message.voice.file_id
            file_name = f"voice_{message.chat.id}.ogg"
        elif message.audio:
            file_id = message.audio.file_id
            orig_name = getattr(message.audio, 'file_name', '')
            ext = os.path.splitext(orig_name)[1].lower() if orig_name else '.mp3'
            file_name = f"audio_{message.chat.id}{ext}"
        else:
            bot.reply_to(message, "❌ Format supported nahi hai.")
            return

        # 2. Telegram Server se file download karo
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # 3. Groq Whisper Call (Response Format: JSON se text safe extract hoga)
        with open(file_name, "rb") as audio_file:
            transcription_data = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="json"  # Safe transfer format
            )

        # 4. Text Content Extract Karo
        if hasattr(transcription_data, 'text'):
            transcription_text = transcription_data.text
        elif isinstance(transcription_data, dict):
            transcription_text = transcription_data.get("text", "")
        else:
            transcription_text = str(transcription_data)

        if not transcription_text or transcription_text.strip() == "":
            bot.reply_to(message, "❌ Mujhe is audio me koi clear aawaz sunai nahi di. Kripya thoda saaf aur lamba audio record karein.")
            return

        # 5. Llama-3 AI Engine Notes Making
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

        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{completion.choices[0].message.content}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me dikkat aayi.")
        print(f"Error Log: {e}")
        
    finally:
        # File Cleanup logic
        if file_name and os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception:
                pass

if __name__ == '__main__':
    bot.polling(none_stop=True)
