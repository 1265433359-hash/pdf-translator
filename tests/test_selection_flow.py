import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import fitz
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint
from pdf_translator.pdf_view import PdfView
from pdf_translator.pdf_document import PdfDocument


def _app():
    return QApplication.instance() or QApplication([])


def test_flow_selection_spans_whole_paragraph(tmp_path):
    _app()
    d = fitz.open(); p = d.new_page()
    p.insert_text((72, 100), "The quick brown fox")
    p.insert_text((72, 120), "jumps over the lazy dog")
    p.insert_text((72, 140), "near the river bank")
    path = tmp_path / "p.pdf"; d.save(str(path)); d.close()

    v = PdfView(); v.load(PdfDocument.open(str(path)))
    z = v._zoom
    words = sorted(v._doc.page_words(0), key=lambda w: (w[5], w[6], w[7]))
    first, last = words[0], words[-1]
    start = QPoint(int(first[0] * z), int((first[1] + first[3]) / 2 * z))
    end = QPoint(int(last[2] * z), int((last[1] + last[3]) / 2 * z))
    text, _ = v._collect_selection(start, end)
    # reading-order flow selection grabs every word across all three lines
    for w in ["quick", "jumps", "river", "bank"]:
        assert w in text, f"{w!r} missing from {text!r}"
