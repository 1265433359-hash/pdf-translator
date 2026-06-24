from pdf_translator.pdf_document import PdfDocument

def test_open_and_read(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    assert d.page_count == 1
    assert "Hello world" in d.page_text(0)
    assert d.has_text_layer() is True
    assert len(d.page_words(0)) > 0

def test_page_blocks_returns_blocks(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    blocks = d.page_blocks(0)
    assert len(blocks) >= 1
    # text blocks carry their text at index 4 and block type at index 6
    assert any(b[6] == 0 and b[4].strip() for b in blocks)

def test_render_returns_image(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    img = d.render_page(0, zoom=1.5)
    assert img.width() > 0 and img.height() > 0

def test_search_finds_hits(sample_pdf):
    d = PdfDocument.open(sample_pdf)
    hits = d.search("test")
    assert len(hits) >= 1 and hits[0][0] == 0
