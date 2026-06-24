import sqlite3, hashlib
from pdf_translator import paths


class TranslationCache:
    def __init__(self, db_path=None):
        self.path = str(db_path or paths.cache_db())
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT)")
        self._conn.commit()

    @staticmethod
    def _key(text, model):
        return hashlib.sha256(f"{text}||{model}".encode("utf-8")).hexdigest()

    def get(self, text, model):
        row = self._conn.execute("SELECT v FROM cache WHERE k=?", (self._key(text, model),)).fetchone()
        return row[0] if row else None

    def put(self, text, model, translation):
        self._conn.execute("INSERT OR REPLACE INTO cache VALUES (?,?)", (self._key(text, model), translation))
        self._conn.commit()

    def size_bytes(self) -> int:
        import os
        return os.path.getsize(self.path) if os.path.exists(self.path) else 0

    def clear(self):
        self._conn.execute("DELETE FROM cache"); self._conn.commit()
        self._conn.execute("VACUUM"); self._conn.commit()
