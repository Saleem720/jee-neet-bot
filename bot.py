# Yeh line aapke file me sabse UPAR (jahan baki imports hain) honi chahiye
import os
from groq import Groq

# Jaha aapka Groq client initialize ho raha hai (Yeh kisi function ke andar nahi hoga, bahar hoga)
groq_client = Groq(api_key="YOUR_GROQ_API_KEY")


# BAQI CODE KE NICHE YEH HANDLER BILKUL AISE HI PASTE KAREIN:
@bot.message_handler(content_types=['voice', 'audio'])
def handle_student_voice(message):
    bot.reply_to(message, "⏳ Aapki voice note mil gayi hai! Tutorbhai AI isko short notes me badal raha hai...")

    try:
        # Telegram se audio download karne ka process
        file_info = bot.get_file(message.voice.file_id if message.voice else message.audio.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = f"voice_{message.chat.id}.ogg"
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Groq Whisper se audio ko text me badlein
        with open(file_name, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(file_name, audio_file.read()),
                model="whisper-large-v3",
                response_format="text"
            )

        # AI se bheege hue text ka summary banwayein
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

        # Student ko reply dein
        bot.reply_to(message, f"📝 **Tutorbhai Short Notes:**\n\n{ai_notes}")
        
        # Audio file delete karein
        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me thodi dikkat aayi. Kripya dobara koshish karein.")
        if os.path.exists(file_name):
            os.remove(file_name)
