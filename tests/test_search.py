import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_live_search_highlight_navigate_clear(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path)); monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    _app()
    d = fitz.open()
    d.new_page().insert_text((72, 100), "apple banana apple")
    d.new_page().insert_text((72, 100), "cherry apple")
    p = tmp_path / "s.pdf"; d.save(str(p)); d.close()
    w = MainWindow(); w._open_path(str(p))

    w._on_search_text("apple")                 # live
    assert len(w._search_hits) == 3
    assert len(w.view._highlights.get(0, [])) == 2   # page 0 has two

    w._search_goto(0); assert w.view.current_index == 0
    w._search_goto(w._search_idx + 1)
    w._search_goto(w._search_idx + 1)
    assert w.view.current_index == 1            # third match is on page 1
    w._search_goto(w._search_idx + 1)           # wraps back to first
    assert w._search_idx == 0

    w._on_search_text("")                       # clear cancels
    assert w.view._highlights == {}
    assert w.search_count.text() == ""
