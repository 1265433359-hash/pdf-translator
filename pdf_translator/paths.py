import os
import sys
from pathlib import Path

APP = "PDFTranslator"


def config_dir() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    d = base / APP
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_local_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    d = base / APP
    d.mkdir(parents=True, exist_ok=True)
    return d


def bundled_data_dir() -> Path:
    # Under PyInstaller the bundle root is exposed as sys._MEIPASS; in a normal
    # run that attribute is absent so we fall back to the repo layout.
    base = getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)
    return Path(base) / "data"


def config_file() -> Path:
    return config_dir() / "config.json"


def cache_db() -> Path:
    return data_local_dir() / "cache.db"


def vocab_db() -> Path:
    return data_local_dir() / "vocab.db"


def ecdict_db() -> Path:
    return bundled_data_dir() / "ecdict_lite.db"
