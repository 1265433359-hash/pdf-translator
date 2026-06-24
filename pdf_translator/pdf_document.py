import fitz
from PySide6.QtGui import QImage

class PdfDocument:
    def __init__(self, doc):
        self._doc = doc

    @classmethod
    def open(cls, path: str) -> "PdfDocument":
        return cls(fitz.open(path))

    @property
    def page_count(self) -> int:
        return self._doc.page_count

    def render_page(self, index: int, zoom: float = 1.0) -> QImage:
        page = self._doc[index]
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        return QImage(pix.samples, pix.width, pix.height,
                      pix.stride, QImage.Format.Format_RGB888).copy()

    def page_text(self, index: int) -> str:
        return self._doc[index].get_text("text")

    def page_words(self, index: int) -> list[tuple]:
        return self._doc[index].get_text("words")

    def page_blocks(self, index: int) -> list[tuple]:
        return self._doc[index].get_text("blocks")

    def search(self, text: str) -> list[tuple]:
        hits = []
        for i in range(self.page_count):
            for r in self._doc[i].search_for(text):
                hits.append((i, r))
        return hits

    def has_text_layer(self) -> bool:
        for i in range(self.page_count):
            if self._doc[i].get_text("text").strip():
                return True
        return False
