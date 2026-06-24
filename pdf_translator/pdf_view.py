from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QRect


class PdfView(QScrollArea):
    selection_made = Signal(str, QRect)

    def __init__(self):
        super().__init__()
        self._label = QLabel(); self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self._label); self.setWidgetResizable(True)
        self._doc = None; self.current_index = 0; self._zoom = 1.5
        self._highlights = {}

    def highlight(self, index, rects):
        self._highlights = {index: rects}; self.goto(index)

    def load(self, doc):
        self._doc = doc; self.current_index = 0; self._render()

    def goto(self, index: int):
        if not self._doc: return
        self.current_index = max(0, min(index, self._doc.page_count - 1)); self._render()

    def set_zoom(self, z: float):
        self._zoom = max(0.3, min(z, 5.0)); self._render()

    def fit_width(self):
        if not self._doc: return
        img = self._doc.render_page(self.current_index, 1.0)
        avail = self.viewport().width() - 24
        if img.width(): self.set_zoom(avail / img.width())

    def _render(self):
        if not self._doc: return
        img = self._doc.render_page(self.current_index, self._zoom)
        pm = QPixmap.fromImage(img)
        for r in self._highlights.get(self.current_index, []):
            p = QPainter(pm); p.fillRect(int(r.x0 * self._zoom), int(r.y0 * self._zoom),
                int((r.x1 - r.x0) * self._zoom), int((r.y1 - r.y0) * self._zoom), QColor(255, 235, 59, 90)); p.end()
        self._label.setPixmap(pm)
