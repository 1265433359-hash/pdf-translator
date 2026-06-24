import json, keyring
from dataclasses import dataclass, asdict, field, fields
from pdf_translator import paths

SERVICE = "PDFTranslator"

@dataclass
class Settings:
    engine: str = "deepseek"
    model: str = ""
    theme: str = "cream"
    prompt: str = ""
    concurrency: int = 2  # conservative default; raise in 设置 if your tier allows
    custom_base_url: str = ""
    use_llm: bool = True       # show 大模型 translation source
    use_youdao: bool = False   # show 有道词典 translation source (needs appKey/secret)
    win_w: int = 1200
    win_h: int = 800
    win_max: bool = False

    @classmethod
    def load(cls) -> "Settings":
        p = paths.config_file()
        if p.exists():
            known = {f.name for f in fields(cls)}
            loaded = {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
                      if k in known}
            return cls(**{**asdict(cls()), **loaded})
        return cls()

    def save(self):
        paths.config_file().write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def get_api_key(self, engine: str) -> str:
        return keyring.get_password(SERVICE, engine) or ""

    def set_api_key(self, engine: str, key: str):
        keyring.set_password(SERVICE, engine, key)
