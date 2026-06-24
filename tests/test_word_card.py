import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sqlite3

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


def _app():
    return QApplication.instance() or QApplication([])


def _make_ecdict(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE dict (word TEXT, phonetic TEXT, translation TEXT)")
    conn.execute("INSERT INTO dict VALUES (?,?,?)",
                 ("run", "rʌn", "v. 跑；运行\\nn. 奔跑"))
    conn.commit()
    conn.close()


def test_word_card_found_enrich_and_fallback(tmp_path):
    app = _app()

    db = tmp_path / "ecdict.db"
    _make_ecdict(str(db))

    w = MainWindow()
    w.dictionary = Dictionary(str(db))
    w.cache = None
    # Enrich path gates on a configured API key; pretend one exists so the
    # async enrichment runs deterministically with the fake engine.
    w.settings.get_api_key = lambda engine: "test-key"

    # --- found path: base info shows instantly, then enrich adds collocation ---
    enriched = WordEntry(word="run", collocations=["run out of", "run away"],
                         examples=["I run every day."])
    fake = FakeEngine(enriched)
    w._current_engine = lambda: fake

    w._pending = "run"
    w._show_word_card("run")
    app.processEvents()
    body = w.pane.current_text()
    assert "跑" in body, f"meaning missing from pane: {body!r}"

    # wait for the async enrich worker, then refresh
    w._enrich_worker.wait(5000)
    app.processEvents()
    body2 = w.pane.current_text()
    assert "run out of" in body2, f"collocation not merged: {body2!r}"

    # --- not-found path: missing word falls back to pane translation ---
    w._pending = "zzznotaword"
    w._show_word_card("zzznotaword")
    w._worker.wait(5000)
    app.processEvents()
    assert w.pane.stream_text() == "回退译文"


def test_word_card_no_api_key_skips_enrich_silently(tmp_path):
    """Offline ECDICT-only use must not start enrichment or pop a dialog."""
    app = _app()

    db = tmp_path / "ecdict.db"
    _make_ecdict(str(db))

    w = MainWindow()
    w.dictionary = Dictionary(str(db))
    w.cache = None
    w.settings.get_api_key = lambda engine: ""  # no key configured

    # If enrich were attempted, _current_engine would be called; fail loudly.
    def _boom():
        raise AssertionError("_current_engine must not be called when no key")
    w._current_engine = _boom

    w._pending = "run"
    w._show_word_card("run")
    app.processEvents()

    assert "跑" in w.pane.current_text()
    assert getattr(w, "_enrich_worker", None) is None
