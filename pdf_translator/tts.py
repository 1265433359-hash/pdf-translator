import threading


def speak(word: str, engine=None):
    """Speak a word. Injected engine -> call directly (tests). Otherwise create a
    FRESH pyttsx3 engine on a background thread.

    Why fresh每次: reusing one pyttsx3 engine across calls makes the 2nd
    runAndWait() silently do nothing on Windows SAPI5. A new engine per call
    avoids that; the thread keeps the GUI responsive.
    """
    if engine is not None:
        engine.say(word)
        engine.runAndWait()
        return

    def _run():
        try:
            import pyttsx3
            eng = pyttsx3.init()
            try:
                eng.setProperty("volume", 1.0)  # max software volume
            except Exception:
                pass
            eng.say(word)
            eng.runAndWait()
            eng.stop()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
