import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication, QLabel
from pdf_translator.app_window import MainWindow
from pdf_translator.pdf_document import PdfDocument
from pdf_translator.translation_pane import TranslationPane


class FakeEngine:
    """No-network engine: returns a deterministic ZH-prefixed translation."""
    def translate(self, text, target="zh"):
        return "ZH:" + text


def _app():
    return QApplication.instance() or QApplication([])


def _multi_para_pdf(tmp_path):
    doc = fitz.open()
    page = doc.new_page()
    # Two reasonably long blocks so paragraphs_from_blocks keeps them
    # (it drops blocks with <= 3 words as headers/footers).
    page.insert_text((72, 100), "The quick brown fox jumps over the lazy dog repeatedly.")
    page.insert_text((72, 200), "A second paragraph with several meaningful words here too.")
    p = tmp_path / "multi.pdf"
    doc.save(str(p)); doc.close()
    return str(p)


def test_translation_pane_set_paragraphs(tmp_path):
    _app()
    pane = TranslationPane()
    pane.set_paragraphs(["你好", "世界"])
    labels = pane._host.findChildren(QLabel)
    assert [l.text() for l in labels] == ["你好", "世界"]
    pane.clear()
    assert pane._lay.count() == 0


def test_translate_current_page_offscreen(tmp_path):
    app = _app()
    w = MainWindow()
    w.cache = None  # avoid sqlite cache interference

    doc = PdfDocument.open(_multi_para_pdf(tmp_path))
    w.view.load(doc)
    w._page_count = doc.page_count

    # Inject a fake engine (no network).
    w._current_engine = lambda: FakeEngine()

    # Sanity: preprocessing yields paragraphs to translate.
    paras = w._page_paragraphs(w.view.current_index)
    assert len(paras) >= 1

    # Trigger the real current-page translation logic and wait for the worker.
    w._translate_page()
    assert w._batch_worker.wait(5000), "batch worker did not finish in time"
    app.processEvents()

    labels = w.pane._host.findChildren(QLabel)
    texts = [l.text() for l in labels]
    assert len(texts) >= 1, "pane received no translated paragraphs"
    assert all(t.startswith("ZH:") for t in texts)
