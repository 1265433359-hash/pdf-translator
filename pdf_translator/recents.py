"""Recently-opened PDF history, persisted to config_dir/recents.json."""
import json
from pdf_translator import paths

LIMIT = 12


def _file():
    return paths.config_dir() / "recents.json"


def all_recents(limit=LIMIT):
    f = _file()
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return [p for p in data if isinstance(p, str)][:limit]


def add_recent(path, limit=LIMIT):
    """Move `path` to the front of the recents list and persist; returns the list."""
    path = str(path)
    items = [p for p in all_recents(limit=100) if p != path]
    items.insert(0, path)
    items = items[:limit]
    try:
        _file().write_text(json.dumps(items, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    except OSError:
        pass
    return items


def remove_recent(path):
    items = [p for p in all_recents(limit=100) if p != str(path)]
    try:
        _file().write_text(json.dumps(items, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    except OSError:
        pass
    return items
