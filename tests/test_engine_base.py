from pdf_translator.engines.base import Translator, WordEntry


class Dummy(Translator):
    def translate(self, text, target="zh"):
        return "译:" + text


def test_default_stream_yields_full():
    d = Dummy()
    assert "".join(d.translate_stream("hi")) == "译:hi"


def test_word_entry_fields():
    w = WordEntry(word="run", phonetic="rʌn", meanings=["跑"], collocations=["run out"], examples=[])
    assert w.word == "run" and w.collocations == ["run out"]
