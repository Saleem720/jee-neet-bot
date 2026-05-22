import os
import telebot
from groq import Groq

# API Keys Setup
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id, 
        "🎓 **Welcome to Tutorbhai Bot!**\n\nMujhe koi bhi voice note ya educational audio file bhejo, main uske short notes bana dunga.",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['voice', 'audio'])
def handle_audio(message):
    bot.reply_to(message, "⏳ Audio mil gaya! Tutorbhai AI isko process kar raha hai...")
    
    # Dynamic temp file naming
    file_name = f"temp_{message.chat.id}.ogg"
    
    try:
        # File id fetch injection logic
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_name, 'wb') as f:
            f.write(downloaded_file)
            
        # Groq Whisper API Translation call
        with open(file_name, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3"
            )
            
        text_content = transcription.text
        
        if not text_content.strip():
            bot.reply_to(message, "❌ Audio mein kuch sunai nahi diya.")
            return
            
        # Llama-3 Short Notes Generation Engine
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Aap Tutorbhai ke helpful assistant ho. Diye gaye text se educational short notes banao Hinglish mein."},
                {"role": "user", "content": text_content}
            ]
        )
        
        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{completion.choices[0].message.content}")
        
    except Exception as e:
        bot.reply_to(message, "❌ Ohho! Is baar network ya system error aaya hai. Ek baar bot restart karke dekhein.")
        print(f"Error Logged: {e}")
        
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

if __name__ == '__main__':
    print("Bot starting fresh...")
    # none_stop=True ke sath purane conflicts clear karne ke liye timeout lagaya hai
    bot.polling(none_stop=True, timeout=60)
