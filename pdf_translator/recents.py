"""Recently-opened PDF history with timestamps, persisted to config_dir/recents.json."""
import json
import time
from pdf_translator import paths

LIMIT = 20


def _file():
    return paths.config_dir() / "recents.json"


def _load():
    f = _file()
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    out = []
    for it in data:
        if isinstance(it, dict) and it.get("path"):
            out.append({"path": it["path"], "ts": float(it.get("ts", 0)),
                        "page": int(it.get("page", 0))})
        elif isinstance(it, str):  # tolerate the old path-only format
            out.append({"path": it, "ts": 0.0, "page": 0})
    return out


def _save(items):
    try:
        _file().write_text(json.dumps(items, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    except OSError:
        pass


def all_recents(limit=LIMIT):
    """List of {'path': str, 'ts': float}, most-recent first."""
    return _load()[:limit]


def add_recent(path, ts=None, limit=LIMIT):
    path = str(path)
    items = _load()
    page = next((it["page"] for it in items if it["path"] == path), 0)  # keep last page
    items = [it for it in items if it["path"] != path]
    items.insert(0, {"path": path, "ts": time.time() if ts is None else float(ts),
                     "page": page})
    items = items[:limit]
    _save(items)
    return items


def page_for(path):
    return next((it["page"] for it in _load() if it["path"] == str(path)), 0)


def set_page(path, page):
    items = _load()
    for it in items:
        if it["path"] == str(path):
            it["page"] = int(page)
            _save(items)
            return


def remove_recent(path):
    items = [it for it in _load() if it["path"] != str(path)]
    _save(items)
    return items


def clear():
    _save([])
