from pdf_translator import themes


def test_available_and_load():
    names = themes.available_themes()
    assert "cream" in names
    assert "QWidget" in themes.load_qss("cream")
