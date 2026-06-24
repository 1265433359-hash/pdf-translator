"""用法: python scripts/prepare_ecdict.py path/to/ecdict.csv
ECDICT 源: https://github.com/skywind3000/ECDICT (stardict.csv / ecdict.csv)
仅保留有 translation 的词，控制体积。"""
import csv, sqlite3, sys
from pathlib import Path

def main(csv_path):
    out = Path(__file__).resolve().parent.parent / "data" / "ecdict_lite.db"
    conn = sqlite3.connect(out)
    conn.execute("CREATE TABLE IF NOT EXISTS dict (word TEXT PRIMARY KEY, phonetic TEXT, translation TEXT, pos TEXT)")
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tr = (row.get("translation") or "").strip()
            if not tr: continue
            conn.execute("INSERT OR REPLACE INTO dict VALUES (?,?,?,?)",
                (row["word"].lower(), row.get("phonetic",""), tr, row.get("pos","")))
    conn.commit(); conn.close()
    print("written", out)

if __name__ == "__main__":
    main(sys.argv[1])
