import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow


def _app():
    return QApplication.instance() or QApplication([])


def test_outline_populates_and_navigates(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path)); monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    _app()
    d = fitz.open()
    for i in range(5):
        d.new_page().insert_text((72, 100), f"page {i}")
    d.set_toc([[1, "Intro", 1], [2, "Background", 2], [1, "Method", 4]])
    p = tmp_path / "toc.pdf"; d.save(str(p)); d.close()

    w = MainWindow(); w._open_path(str(p))
    assert w.outline_tree.topLevelItemCount() == 2
    top0 = w.outline_tree.topLevelItem(0)
    assert top0.text(0) == "Intro" and top0.childCount() == 1
    w._on_outline_clicked(w.outline_tree.topLevelItem(1), 0)  # Method -> page 4
    assert w.view.current_index == 3


def test_no_outline_hides_dock(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path)); monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    _app()
    d = fitz.open(); d.new_page().insert_text((72, 100), "x")
    p = tmp_path / "notoc.pdf"; d.save(str(p)); d.close()
    w = MainWindow(); w._open_path(str(p))
    assert w.outline_tree.topLevelItemCount() == 0
