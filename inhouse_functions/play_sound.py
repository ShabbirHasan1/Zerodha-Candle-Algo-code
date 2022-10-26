import pyttsx3

def PlaySound(msg, speed=160, voice=1, volume=1):
    """
    speed - normal = 160, fast > 160, slow < 160 
    voice - 0 for male, 1 for female
    volume - between 0 and 1 , max=1, min=0
    """
    engine = pyttsx3.init()
    engine.setProperty("rate", speed)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[voice].id)
    engine.setProperty('volume',volume)
    engine.say(msg)
    engine.runAndWait()