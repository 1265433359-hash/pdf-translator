import sqlite3
from pdf_translator import paths
from pdf_translator.engines.base import WordEntry

class Dictionary:
    def __init__(self, db_path=None):
        self._conn = sqlite3.connect(str(db_path or paths.ecdict_db()))
    def lookup(self, word) -> WordEntry | None:
        row = self._conn.execute(
            "SELECT phonetic, translation FROM dict WHERE word=?", (word.lower().strip(),)).fetchone()
        if not row: return None
        phonetic, tr = row
        meanings = [ln.strip() for ln in tr.replace("\\n", "\n").split("\n") if ln.strip()]
        return WordEntry(word=word, phonetic=phonetic or "", meanings=meanings)
