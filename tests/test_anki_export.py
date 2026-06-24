from pdf_translator.anki_export import export_csv

def test_export_csv(tmp_path):
    rows = [{"word":"run","phonetic":"rʌn","meanings":["跑"],"examples":["I run."]}]
    out = tmp_path / "anki.txt"; export_csv(rows, out)
    content = out.read_text(encoding="utf-8")
    assert "run\t" in content and "rʌn" in content and "跑" in content
