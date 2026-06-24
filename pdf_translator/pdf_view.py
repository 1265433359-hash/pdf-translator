from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, Signal, QRect, QEvent


class PdfView(QScrollArea):
    selection_made = Signal(str, QRect)

    def __init__(self):
        super().__init__()
        self._label = QLabel(); self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWidget(self._label); self.setWidgetResizable(True)
        self._doc = None; self.current_index = 0; self._zoom = 1.5
        self._highlights = {}
        self._sel_start = None
        self._label.setMouseTracking(True)
        self._label.installEventFilter(self)

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

    def _pixmap_offset(self):
        """Top-left of the pixmap within the label (AlignCenter centering margin)."""
        pm = self._label.pixmap()
        if pm is None or pm.isNull():
            return 0, 0
        ox = max(0, (self._label.width() - pm.width()) // 2)
        oy = max(0, (self._label.height() - pm.height()) // 2)
        return ox, oy

    def _to_pdf(self, label_pos):
        """Map a point in label coordinates to PDF-space coordinates."""
        ox, oy = self._pixmap_offset()
        return (label_pos.x() - ox) / self._zoom, (label_pos.y() - oy) / self._zoom

    def _collect_selection(self, start, end):
        """Collect words whose fitz bbox falls inside the PDF-space selection box.

        start/end are points in label coordinate space.
        Returns (text, QRect) where QRect is in label coordinates.
        """
        if not self._doc:
            return "", QRect(start, end)
        sx, sy = self._to_pdf(start)
        ex, ey = self._to_pdf(end)
        x0, x1 = min(sx, ex), max(sx, ex)
        y0, y1 = min(sy, ey), max(sy, ey)
        words = [w[4] for w in self._doc.page_words(self.current_index)
                 if w[0] >= x0 - 2 and w[2] <= x1 + 2 and w[1] >= y0 - 2 and w[3] <= y1 + 2]
        text = " ".join(words).strip()
        return text, QRect(start, end)

    def eventFilter(self, obj, e):
        if obj is self._label and getattr(self, "_doc", None) is not None:
            if e.type() == QEvent.Type.MouseButtonPress and e.button() == Qt.MouseButton.LeftButton:
                self._sel_start = e.position().toPoint()
                return False
            if e.type() == QEvent.Type.MouseButtonRelease and e.button() == Qt.MouseButton.LeftButton:
                if self._sel_start is not None:
                    end = e.position().toPoint()
                    text, rect = self._collect_selection(self._sel_start, end)
                    self._sel_start = None
                    if text:
                        self.selection_made.emit(text, rect)
                return False
        return super().eventFilter(obj, e)
