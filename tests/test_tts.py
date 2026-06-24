from pdf_translator import tts


def test_speak_calls_engine():
    calls = []
    class Fake:
        def say(self, t): calls.append(t)
        def runAndWait(self): calls.append("run")
    tts.speak("hello", engine=Fake())
    assert calls == ["hello", "run"]
