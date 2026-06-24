import json, keyring
from dataclasses import dataclass, asdict, field
from pdf_translator import paths

SERVICE = "PDFTranslator"

@dataclass
class Settings:
    engine: str = "deepseek"
    model: str = ""
    theme: str = "cream"
    prompt: str = ""
    concurrency: int = 4
    custom_base_url: str = ""

    @classmethod
    def load(cls) -> "Settings":
        p = paths.config_file()
        if p.exists():
            return cls(**{**asdict(cls()), **json.loads(p.read_text(encoding="utf-8"))})
        return cls()

    def save(self):
        paths.config_file().write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_api_key(self, engine: str) -> str:
        return keyring.get_password(SERVICE, engine) or ""

    def set_api_key(self, engine: str, key: str):
        keyring.set_password(SERVICE, engine, key)
