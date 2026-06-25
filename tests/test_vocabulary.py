from pdf_translator.vocabulary import Vocabulary
from pdf_translator.engines.base import WordEntry

def test_add_list_remove(tmp_path):
    v = Vocabulary(tmp_path / "v.db")
    v.add(WordEntry("run", "rʌn", ["跑"], [], ["I run."]), source="a.pdf")
    rows = v.all()
    assert len(rows) == 1 and rows[0]["word"] == "run"
    v.remove("run")
    assert v.count() == 0


def test_is_saved_forgot_and_sort(tmp_path):
    from pdf_translator.vocabulary import Vocabulary
    from pdf_translator.engines.base import WordEntry
    v = Vocabulary(tmp_path / "v2.db")
    v.add(WordEntry("alpha", "", ["甲"]), source="a.pdf")
    v.add(WordEntry("zulu", "", ["祖"]), source="b.pdf")
    assert v.is_saved("alpha") and not v.is_saved("missing")
    # forgot counting
    assert v.forgot_count("zulu") == 0
    v.increment_forgot("zulu"); v.increment_forgot("zulu")
    assert v.forgot_count("zulu") == 2
    # adding an existing word must NOT reset its forgot count
    v.add(WordEntry("zulu", "", ["祖鲁"]))
    assert v.forgot_count("zulu") == 2
    # default sort = forgot desc -> zulu first
    assert [r["word"] for r in v.all()] == ["zulu", "alpha"]
    # alpha sort
    assert [r["word"] for r in v.all(sort="alpha")] == ["alpha", "zulu"]
    # forgot tie broken by earliest collected (alpha added before a later one)
    v.add(WordEntry("beta", "", ["乙"]))
    order = [r["word"] for r in v.all(sort="forgot")]
    assert order[0] == "zulu"                 # most forgotten first
    assert order.index("alpha") < order.index("beta")  # tie -> earlier first
