from gtts import gTTS

text = "News today. Paper boy enroute to deliver the morning paper. The sun is shining and the birds are singing. It's a beautiful day to be alive."
tts = gTTS(text=text, lang="en", slow=False)
tts.save("output.mp3")