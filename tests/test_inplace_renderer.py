import fitz
from pdf_translator.inplace_renderer import render_inplace


def test_inplace_replaces_text(tmp_path):
    doc = fitz.open(); page = doc.new_page()
    page.insert_text((72, 72), "Hello")
    rect = fitz.Rect(72, 60, 300, 90)
    pix = render_inplace(page, [(rect, "你好")])
    assert pix.width > 0
    # 重新读页文本：原 Hello 应被覆盖
    assert "Hello" not in page.get_text("text")
