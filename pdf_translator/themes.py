from pdf_translator import paths


def _dir():
    return paths.bundled_data_dir() / "themes"


def available_themes() -> list[str]:
    return sorted(p.stem for p in _dir().glob("*.qss"))


def load_qss(name) -> str:
    return (_dir() / f"{name}.qss").read_text(encoding="utf-8")


def apply_theme(app, name):
    app.setStyleSheet(load_qss(name))
