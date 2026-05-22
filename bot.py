import os
import requests
import telebot
from groq import Groq

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)


@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_text = (
        "🎓 **Welcome to Tutorbhai Bot!**\n\n"
        "Main aapki padhai asaan banane ke liye tayaar hoon.\n"
        "🎙️ **Voice Note ya Audio Bhejo:** Main turant uske mast short notes bana dunga!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')


@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    bot.reply_to(message, "⏳ Audio mil gaya! Tutorbhai AI isko process kar raha hai...")
    
    try:
        # 1. Handle Voice Note vs Audio File ID
        if message.voice:
            file_id = message.voice.file_id
            filename = "voice.mp3"  # Force bypass extension for transcription server
        elif message.audio:
            file_id = message.audio.file_id
            orig_name = getattr(message.audio, 'file_name', '')
            ext = os.path.splitext(orig_name)[1].lower() if orig_name else '.mp3'
            filename = f"audio{ext}"
        else:
            return

        # 2. Telegram se file direct download karo bytes stream mein
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        audio_response = requests.get(file_url)
        if audio_response.status_code != 200:
            raise Exception("Telegram content fetch failed.")

        # 3. Direct HTTP POST Requests ke zariye Groq API endpoint par file data stream karna
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}"
        }
        files = {
            "file": (filename, audio_response.content, "audio/mpeg")
        }
        data = {
            "model": "whisper-large-v3",
            "response_format": "json"
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code != 200:
            raise Exception(f"Groq API HTTP Error: {response.text}")

        transcription_json = response.json()
        transcription_text = transcription_json.get("text", "")

        if not transcription_text or transcription_text.strip() == "":
            bot.reply_to(message, "❌ Is audio me mujhe koi saaf aawaz sunai nahi di. Kripya thoda lamba aur saaf bol kar bhejein.")
            return

        # 4. Llama-3 AI Engine se Notes create karwana
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
        bot.reply_to(message, "❌ Ohho! Is baar network ya system error aaya hai. Ek baar bot restart karke dekhein.")
        print(f"Server Logged Exception: {e}")


if __name__ == '__main__':
    print("Tutorbhai Bot Engine Active...")
    bot.polling(none_stop=True, timeout=60)
