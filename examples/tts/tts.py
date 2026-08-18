import pyttsx3

engine = pyttsx3.init()

# engine.say("Hello, I am your text to speech assistant. What would you like me to say? Also, did you know that I am doing this completely offline?")
engine.save_to_file("This audio is captured straight to a file.", "output.wav")
engine.runAndWait()