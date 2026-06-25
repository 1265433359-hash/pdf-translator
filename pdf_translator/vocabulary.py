import sqlite3
import json
import time
from pdf_translator import paths


class Vocabulary:
    def __init__(self, db_path=None):
        self._conn = sqlite3.connect(str(db_path or paths.vocab_db()),
                                     check_same_thread=False)
        self._conn.execute("""CREATE TABLE IF NOT EXISTS vocab
            (word TEXT PRIMARY KEY, phonetic TEXT, meanings TEXT, examples TEXT,
             source TEXT, forgot INTEGER DEFAULT 0, added_at REAL DEFAULT 0)""")
        # migrate older DBs that lack the new columns
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(vocab)")}
        if "forgot" not in cols:
            self._conn.execute("ALTER TABLE vocab ADD COLUMN forgot INTEGER DEFAULT 0")
        if "added_at" not in cols:
            self._conn.execute("ALTER TABLE vocab ADD COLUMN added_at REAL DEFAULT 0")
        self._conn.commit()

    def add(self, entry, source=""):
        """Insert if new (keeps existing forgot/added_at on a duplicate add)."""
        if self.is_saved(entry.word):
            return
        self._conn.execute(
            "INSERT INTO vocab (word, phonetic, meanings, examples, source, forgot, added_at)"
            " VALUES (?,?,?,?,?,0,?)",
            (entry.word, entry.phonetic,
             json.dumps(entry.meanings, ensure_ascii=False),
             json.dumps(entry.examples, ensure_ascii=False), source, time.time()))
        self._conn.commit()

    def is_saved(self, word) -> bool:
        return self._conn.execute("SELECT 1 FROM vocab WHERE word=?", (word,)).fetchone() is not None

    def forgot_count(self, word) -> int:
        row = self._conn.execute("SELECT forgot FROM vocab WHERE word=?", (word,)).fetchone()
        return int(row[0]) if row else 0

    def increment_forgot(self, word):
        self._conn.execute("UPDATE vocab SET forgot = forgot + 1 WHERE word=?", (word,))
        self._conn.commit()

    _SORTS = {
        # default: most-forgotten first, ties broken by earliest collected
        "forgot": "ORDER BY forgot DESC, added_at ASC",
        "alpha": "ORDER BY word COLLATE NOCASE ASC",
        "time": "ORDER BY added_at DESC",
    }

    def all(self, sort="forgot"):
        order = self._SORTS.get(sort, self._SORTS["forgot"])
        cur = self._conn.execute(
            "SELECT word, phonetic, meanings, examples, source, forgot, added_at "
            "FROM vocab " + order)
        return [{"word": w, "phonetic": p, "meanings": json.loads(m),
                 "examples": json.loads(e), "source": s,
                 "forgot": int(fg or 0), "added_at": float(at or 0)}
                for w, p, m, e, s, fg, at in cur]

    def remove(self, word):
        self._conn.execute("DELETE FROM vocab WHERE word=?", (word,))
        self._conn.commit()

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM vocab").fetchone()[0]
