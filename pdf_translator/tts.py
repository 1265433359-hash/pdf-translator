_engine = None


def _default():
    global _engine
    if _engine is None:
        import pyttsx3; _engine = pyttsx3.init()
    return _engine


def speak(word: str, engine=None):
    eng = engine or _default()
    eng.say(word); eng.runAndWait()
