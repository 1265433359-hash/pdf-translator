import sqlite3, json
from pdf_translator import paths

class Vocabulary:
    def __init__(self, db_path=None):
        self._conn = sqlite3.connect(str(db_path or paths.vocab_db()))
        self._conn.execute("""CREATE TABLE IF NOT EXISTS vocab
            (word TEXT PRIMARY KEY, phonetic TEXT, meanings TEXT, examples TEXT, source TEXT)""")
        self._conn.commit()
    def add(self, entry, source=""):
        self._conn.execute("INSERT OR REPLACE INTO vocab VALUES (?,?,?,?,?)",
            (entry.word, entry.phonetic, json.dumps(entry.meanings, ensure_ascii=False),
             json.dumps(entry.examples, ensure_ascii=False), source))
        self._conn.commit()
    def all(self):
        cur = self._conn.execute("SELECT word, phonetic, meanings, examples, source FROM vocab")
        return [{"word": w, "phonetic": p, "meanings": json.loads(m),
                 "examples": json.loads(e), "source": s} for w, p, m, e, s in cur]
    def remove(self, word):
        self._conn.execute("DELETE FROM vocab WHERE word=?", (word,)); self._conn.commit()
    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM vocab").fetchone()[0]
