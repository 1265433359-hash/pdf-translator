from pdf_translator import paths


def _dir():
    return paths.bundled_data_dir() / "themes"


def available_themes() -> list[str]:
    return sorted(p.stem for p in _dir().glob("*.qss"))


def load_qss(name) -> str:
    return (_dir() / f"{name}.qss").read_text(encoding="utf-8")


def apply_theme(app, name):
    # Never raise on a stale/missing theme: fall back to "cream", then to an
    # empty stylesheet, so a bad settings.theme can't crash startup.
    for candidate in (name, "cream"):
        qss = _dir() / f"{candidate}.qss"
        if qss.exists():
            app.setStyleSheet(qss.read_text(encoding="utf-8"))
            return
    app.setStyleSheet("")
