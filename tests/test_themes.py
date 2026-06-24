from pdf_translator import themes


def test_available_and_load():
    names = themes.available_themes()
    assert "cream" in names
    assert "QWidget" in themes.load_qss("cream")


def test_apply_theme_bogus_name_does_not_raise():
    class FakeApp:
        def __init__(self):
            self.qss = None
        def setStyleSheet(self, qss):
            self.qss = qss

    app = FakeApp()
    # A stale/missing theme must not crash; falls back to cream (non-empty).
    themes.apply_theme(app, "does-not-exist-zzz")
    assert app.qss is not None
