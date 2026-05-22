import os
import telebot
from groq import Groq

# ==========================================
# ⚙️ CONFIGURATION (RAILWAY ENV MATCH)
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
# 🎙️ AUDIO & VOICE HANDLER (SOLID FIX)
# ==========================================
@bot.message_handler(content_types=['voice', 'audio'])
def handle_student_voice(message):
    bot.reply_to(message, "⏳ Aapki voice note mil gayi hai! Tutorbhai AI isko short notes me badal raha hai...")
    
    file_name = None
    
    try:
        # 1. Check karo ki file voice note hai ya dynamic audio file
        if message.voice:
            file_id = message.voice.file_id
            file_name = f"voice_{message.chat.id}.ogg"
        elif message.audio:
            file_id = message.audio.file_id
            # Standard extension select karna core dynamic formats ke liye
            orig_name = getattr(message.audio, 'file_name', '')
            ext = os.path.splitext(orig_name)[1].lower() if orig_name else '.mp3'
            file_name = f"audio_{message.chat.id}{ext}"
        else:
            bot.reply_to(message, "❌ Maaf kijiyega, yeh audio format supported nahi hai.")
            return

        # 2. Telegram API se path nikal kar file download karo
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 3. Stream ko temporary local file mein safe write karna
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        # 4. Groq Whisper call using proper local file pointer
        with open(file_name, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3",
                response_format="text"
            )

        if not transcription or str(transcription).strip() == "":
            bot.reply_to(message, "❌ Mujhe is audio me koi clear aawaz sunai nahi di. Kripya thoda saaf aur lamba audio record karein.")
            return

        # 5. Llama-3 AI power engine logic notes creation
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {
                    "role": "system", 
                    "content": "Aap Tutorbhai Bot ke ek helpful AI assistant hain. Diye gaye educational lecture ke audio text mese important bullet points, key definitions aur summary nikal kar ekdum clean, easy-to-understand Hinglish/English mix notes taiyar karein."
                },
                {
                    "role": "user", 
                    "content": str(transcription)
                }
            ]
        )

        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{completion.choices[0].message.content}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me dikkat aayi.")
        print(f"Railway Server Internal Log: {e}")
        
    finally:
        # Cleanup: Hard disk storage management logic
        if file_name and os.path.exists(file_name):
            try:
                os.remove(file_name)
            except Exception:
                pass

if __name__ == '__main__':
    print("Tutorbhai Engine Active...")
    bot.polling(none_stop=True)
