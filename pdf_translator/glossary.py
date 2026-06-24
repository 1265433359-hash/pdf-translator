import json
from pathlib import Path
from pdf_translator import paths


class Glossary:
    def __init__(self, path=None):
        self._path = Path(path or (paths.config_dir() / "glossary.json"))
        self._d = json.loads(self._path.read_text(encoding="utf-8")) if self._path.exists() else {}

    def _save(self):
        self._path.write_text(json.dumps(self._d, ensure_ascii=False, indent=2), encoding="utf-8")

    def set(self, en, zh):
        self._d[en] = zh
        self._save()

    def remove(self, en):
        self._d.pop(en, None)
        self._save()

    def all(self):
        return dict(self._d)

    def apply_to_prompt(self, base_prompt, text):
        hits = {en: zh for en, zh in self._d.items() if en.lower() in text.lower()}
        if not hits:
            return base_prompt
        terms = "; ".join(f"{en}→{zh}" for en, zh in hits.items())
        return base_prompt + f"\n以下术语必须按指定译法翻译：{terms}。"
