import sqlite3
from pdf_translator.dictionary import Dictionary

def make_db(tmp_path):
    p = tmp_path / "d.db"; c = sqlite3.connect(p)
    c.execute("CREATE TABLE dict (word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)")
    c.execute("INSERT INTO dict VALUES ('run','rʌn','vt. 跑\\nn. 奔跑','v/n')"); c.commit(); c.close()
    return p

def test_lookup(tmp_path):
    d = Dictionary(make_db(tmp_path))
    e = d.lookup("Run")
    assert e and e.phonetic == "rʌn" and any("跑" in m for m in e.meanings)
    assert d.lookup("zzz") is None
