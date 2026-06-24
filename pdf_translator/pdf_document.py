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

    def get_toc(self) -> list:
        """Outline/bookmarks: list of [level, title, page_number(1-based)]."""
        try:
            return self._doc.get_toc()
        except Exception:
            return []

    def has_text_layer(self) -> bool:
        for i in range(self.page_count):
            if self._doc[i].get_text("text").strip():
                return True
        return False

    @property
    def path(self) -> str:
        return self._doc.name

    def annotate(self, index: int, rects, kind: str):
        """Add highlight/strikeout annotations over the given rects on a page.

        rects: iterable of fitz.Rect or (x0,y0,x1,y1) tuples (PDF coordinates).
        kind: 'highlight' or 'strikeout'.
        Returns the list of created annotation objects (for undo).
        """
        page = self._doc[index]
        xrefs = []
        for r in rects:
            rect = fitz.Rect(r)
            if kind == "highlight":
                xrefs.append(page.add_highlight_annot(rect).xref)
            elif kind == "strikeout":
                xrefs.append(page.add_strikeout_annot(rect).xref)
            else:
                raise ValueError(f"unknown annotation kind: {kind}")
        return xrefs

    def delete_annots(self, index: int, xrefs):
        """Delete annotations by xref (stable across Page wrapper instances)."""
        page = self._doc[index]
        want = set(xrefs)
        for a in list(page.annots()):
            if a.xref in want:
                page.delete_annot(a)

    def annotation_count(self, index: int) -> int:
        return sum(1 for _ in self._doc[index].annots())

    def save(self, path: str = None):
        """Persist annotations. Default: incremental save back to the original file."""
        if path is None or path == self.path:
            self._doc.save(self.path, incremental=True,
                           encryption=fitz.PDF_ENCRYPT_KEEP)
        else:
            self._doc.save(path)

    def close(self):
        self._doc.close()
