import fitz, pytest
from pathlib import Path

@pytest.fixture
def sample_pdf(tmp_path) -> str:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello world. This is a test PDF document.")
    p = tmp_path / "sample.pdf"
    doc.save(str(p)); doc.close()
    return str(p)
