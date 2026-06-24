from pdf_translator.vocabulary import Vocabulary
from pdf_translator.engines.base import WordEntry

def test_add_list_remove(tmp_path):
    v = Vocabulary(tmp_path / "v.db")
    v.add(WordEntry("run", "rʌn", ["跑"], [], ["I run."]), source="a.pdf")
    rows = v.all()
    assert len(rows) == 1 and rows[0]["word"] == "run"
    v.remove("run")
    assert v.count() == 0
