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
        
        # Audio file delete karein taaki server full na ho
        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        bot.reply_to(message, "❌ Maaf kijiyega, is audio ko process karne me thodi dikkat aayi. Kripya dobara koshish karein.")
        if os.path.exists(file_name):
            os.remove(file_name)
