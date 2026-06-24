"""用法: python scripts/prepare_ecdict.py path/to/ecdict.csv
ECDICT 源: https://github.com/skywind3000/ECDICT
  - stardict.csv（完整版，约340万词条，最全面，推荐）
  - ecdict.csv（精简版，约77万）
仅保留有 translation 的词。"""
import csv, sqlite3, sys
from pathlib import Path

csv.field_size_limit(50 * 1024 * 1024)  # stardict has very large 'detail' fields

def main(csv_path):
    out = Path(__file__).resolve().parent.parent / "data" / "ecdict_lite.db"
    if out.exists():
        out.unlink()  # rebuild fresh
    conn = sqlite3.connect(out)
    conn.execute("CREATE TABLE IF NOT EXISTS dict (word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)")
    n = 0
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tr = (row.get("translation") or "").strip()
            if not tr:
                continue
            conn.execute("INSERT OR REPLACE INTO dict VALUES (?,?,?,?)",
                (row["word"].lower(), row.get("phonetic", ""), tr, row.get("pos", "")))
            n += 1
            if n % 200000 == 0:
                conn.commit()
    conn.commit(); conn.close()
    print(f"written {out} ({n} entries)")

if __name__ == "__main__":
    main(sys.argv[1])
