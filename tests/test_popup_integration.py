import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sqlite3

from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow
from pdf_translator.dictionary import Dictionary


class FakeEngine:
    def __init__(self, chunks):
        self._chunks = chunks

    def translate_stream(self, text):
        for c in self._chunks:
            yield c


def _app():
    return QApplication.instance() or QApplication([])


def _make_empty_ecdict(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE dict (word TEXT, phonetic TEXT, translation TEXT)")
    conn.commit()
    conn.close()


def test_popup_phrase_pin_and_word_paths(tmp_path):
    app = _app()
    w = MainWindow()

    fake = FakeEngine(["你好", "，", "世界"])
    w._current_engine = lambda: fake
    # avoid sqlite cache interfering with the assertion
    w.cache = None
    # Provision an empty ECDICT so the single-word path deterministically
    # misses and falls back to the popup translation (no machine-state dep).
    db = tmp_path / "ecdict.db"
    _make_empty_ecdict(str(db))
    w.dictionary = Dictionary(str(db))

    # --- phrase path ---
    w._pending = "hello world"
    w._translate_pending()
    w._worker.wait(5000)
    app.processEvents()
    assert w.popup.body.text() == "你好，世界"

    # --- pin to dock ---
    w.popup.pin_btn.setChecked(True)
    app.processEvents()
    assert w._dock is not None, "dock not created on pin"
    assert not w.popup.isVisible(), "popup should hide when pinned"
    assert w._dock_label.text() == "你好，世界"

    # --- single-word path routes through popup (no crash) ---
    w.popup.pin_btn.setChecked(False)
    app.processEvents()
    w.popup.body.setText("")
    fake2 = FakeEngine(["苹果"])
    w._current_engine = lambda: fake2
    w._pending = "apple"
    w._translate_pending()
    w._worker.wait(5000)
    app.processEvents()
    assert w.popup.body.text() == "苹果"
