import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sqlite3, tempfile
from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow
from pdf_translator.dictionary import Dictionary
from pdf_translator.engines.base import WordEntry


class FakeEngine:
    """No-network engine: returns an enriched WordEntry from lookup_word."""
    def __init__(self, entry):
        self._entry = entry
    def lookup_word(self, word):
        return self._entry
    # phrase fallback path uses translate_stream
    def translate_stream(self, text):
        yield "回退译文"


def _make_ecdict(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE dict (word TEXT, phonetic TEXT, translation TEXT)")
    conn.execute("INSERT INTO dict VALUES (?,?,?)",
                 ("run", "rʌn", "v. 跑；运行\\nn. 奔跑"))
    conn.commit(); conn.close()


def run():
    app = QApplication.instance() or QApplication([])

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    _make_ecdict(tmp.name)

    w = MainWindow()
    w.dictionary = Dictionary(tmp.name)
    w.cache = None

    # --- found path: base info shows instantly, then enrich adds collocation ---
    enriched = WordEntry(word="run", collocations=["run out of", "run away"],
                         examples=["I run every day."])
    fake = FakeEngine(enriched)
    w._current_engine = lambda: fake

    w._pending = "run"
    w._show_word_card("run")
    app.processEvents()
    body = w.word_card.body.text()
    assert "跑" in body, f"meaning missing from card: {body!r}"
    print("CARD BASE OK:", repr(body))

    # wait for the async enrich worker, then refresh
    w._enrich_worker.wait(5000)
    app.processEvents()
    body2 = w.word_card.body.text()
    assert "run out of" in body2, f"collocation not merged: {body2!r}"
    print("CARD ENRICH OK:", repr(body2))

    # --- not-found path: missing word falls back to popup translation ---
    w.word_card.hide()
    w.popup.body.setText("")
    w._pending = "zzznotaword"
    w._show_word_card("zzznotaword")
    w._worker.wait(5000)
    app.processEvents()
    pb = w.popup.body.text()
    assert pb == "回退译文", f"fallback popup body was {pb!r}"
    print("FALLBACK OK:", repr(pb))

    print("SMOKE PASS")


if __name__ == "__main__":
    run()
