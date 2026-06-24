import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from pdf_translator.vocabulary import Vocabulary
from pdf_translator.engines.base import WordEntry
from pdf_translator.vocab_dialog import VocabularyDialog


def _app():
    return QApplication.instance() or QApplication([])


def test_vocab_dialog_list_search_delete(tmp_path):
    _app()
    v = Vocabulary(str(tmp_path / "v.db"))
    v.add(WordEntry("ubiquitous", "", ["a. 无所不在的"]))
    v.add(WordEntry("chaos", "", ["n. 混乱"]))
    d = VocabularyDialog(v)
    assert d.table.rowCount() == 2
    d.search.setText("混乱")           # filter by meaning
    assert d.table.rowCount() == 1
    assert d.table.item(0, 0).text() == "chaos"
    d.search.setText("")
    d.table.selectRow(0)
    d._delete()
    assert v.count() == 1
