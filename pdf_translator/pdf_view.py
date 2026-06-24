from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtGui import QPixmap, QPainter, QColor, QImage
from PySide6.QtCore import Qt, Signal, QRect, QEvent


class PdfView(QScrollArea):
    selection_made = Signal(str, QRect)
    page_changed = Signal(int)  # emitted with the new 0-based page index
    context_requested = Signal(object)  # right-click global QPoint, for annotate menu

    def __init__(self):
        super().__init__()
        self._label = QLabel(); self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setCursor(Qt.CursorShape.IBeamCursor)  # text-selection feedback (杠)
        self.setWidget(self._label); self.setWidgetResizable(True)
        self._doc = None; self.current_index = 0; self._zoom = 2.0
        self._dpr = 1.0
        self._highlights = {}
        self._sel_start = None
        self._last_sel_rects = []   # PDF-space (x0,y0,x1,y1) of last selected words
        self._last_sel_page = 0
        self._last_sel_text = ""
        self._sel_overlay = []      # PDF rects to draw as the current selection shadow
        self._sel_overlay_page = -1
        self._label.setMouseTracking(True)
        self._label.installEventFilter(self)

    def last_selection(self):
        """(text, page_index, [pdf_rects]) of the most recent drag-selection."""
        return self._last_sel_text, self._last_sel_page, list(self._last_sel_rects)

    def annotate_selection(self, kind: str) -> bool:
        """Apply a 'highlight'/'strikeout' annotation over the last selection."""
        if not self._doc or not self._last_sel_rects:
            return False
        self._doc.annotate(self._last_sel_page, self._last_sel_rects, kind)
        if self._last_sel_page == self.current_index:
            self._render()
        return True

    def highlight(self, index, rects):
        self._highlights = {index: rects}; self.goto(index)

    def load(self, doc):
        self._doc = doc; self.current_index = 0; self._render()
        self.page_changed.emit(self.current_index)

    def goto(self, index: int):
        if not self._doc: return
        new_index = max(0, min(index, self._doc.page_count - 1))
        changed = new_index != self.current_index
        self.current_index = new_index
        self._render()
        if changed:
            self.page_changed.emit(self.current_index)

    def wheelEvent(self, e):
        """Ctrl+wheel zooms; otherwise scroll the page and flip at the boundaries."""
        if not self._doc:
            return super().wheelEvent(e)
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            dy = e.angleDelta().y()
            if dy > 0:
                self.set_zoom(self._zoom * 1.1)
            elif dy < 0:
                self.set_zoom(self._zoom / 1.1)
            e.accept(); return
        bar = self.verticalScrollBar()
        dy = e.angleDelta().y()
        at_top = bar.value() <= bar.minimum()
        at_bottom = bar.value() >= bar.maximum()
        if dy < 0 and at_bottom and self.current_index < self._doc.page_count - 1:
            self.goto(self.current_index + 1)
            self.verticalScrollBar().setValue(self.verticalScrollBar().minimum())
            e.accept(); return
        if dy > 0 and at_top and self.current_index > 0:
            self.goto(self.current_index - 1)
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
            e.accept(); return
        super().wheelEvent(e)

    def set_zoom(self, z: float):
        self._zoom = max(0.3, min(z, 5.0)); self._render()

    def fit_width(self):
        if not self._doc: return
        img = self._doc.render_page(self.current_index, 1.0)
        avail = self.viewport().width() - 24
        if img.width(): self.set_zoom(avail / img.width())

    def show_fitz_pixmap(self, pix):
        """Display an externally-rendered fitz.Pixmap (e.g. in-place render)."""
        img = QImage(pix.samples, pix.width, pix.height,
                     pix.stride, QImage.Format.Format_RGB888).copy()
        self._label.setPixmap(QPixmap.fromImage(img))

    def _render(self):
        if not self._doc: return
        dpr = self.devicePixelRatioF() or 1.0
        self._dpr = dpr
        scale = self._zoom * dpr  # render at true device pixels for crisp text
        img = self._doc.render_page(self.current_index, scale)
        pm = QPixmap.fromImage(img)  # device-pixel canvas
        for r in self._highlights.get(self.current_index, []):
            p = QPainter(pm); p.fillRect(int(r.x0 * scale), int(r.y0 * scale),
                int((r.x1 - r.x0) * scale), int((r.y1 - r.y0) * scale), QColor(255, 235, 59, 90)); p.end()
        # current selection shadow (live feedback while reading)
        if self._sel_overlay_page == self.current_index:
            for r in self._sel_overlay:
                x0, y0, x1, y1 = r
                p = QPainter(pm); p.fillRect(int(x0 * scale), int(y0 * scale),
                    int((x1 - x0) * scale), int((y1 - y0) * scale), QColor(51, 102, 204, 70)); p.end()
        pm.setDevicePixelRatio(dpr)  # display at logical size -> sharp on HiDPI
        self._label.setPixmap(pm)

    def _pixmap_offset(self):
        """Top-left of the pixmap within the label (AlignCenter centering margin), logical px."""
        pm = self._label.pixmap()
        if pm is None or pm.isNull():
            return 0, 0
        dpr = getattr(self, "_dpr", 1.0) or 1.0
        lw = pm.width() / dpr
        lh = pm.height() / dpr
        ox = max(0, (self._label.width() - lw) / 2)
        oy = max(0, (self._label.height() - lh) / 2)
        return ox, oy

    def _to_pdf(self, label_pos):
        """Map a point in label coordinates to PDF-space coordinates."""
        ox, oy = self._pixmap_offset()
        return (label_pos.x() - ox) / self._zoom, (label_pos.y() - oy) / self._zoom

    def _collect_selection(self, start, end):
        """Collect words whose fitz bbox *overlaps* the PDF-space selection box.

        Uses intersection (not containment) so a rough drag still grabs the words
        it crosses. start/end are points in label coordinate space.
        Returns (text, QRect) where QRect is in label coordinates.
        """
        if not self._doc:
            return "", QRect(start, end)
        sx, sy = self._to_pdf(start)
        ex, ey = self._to_pdf(end)
        x0, x1 = min(sx, ex), max(sx, ex)
        y0, y1 = min(sy, ey), max(sy, ey)
        words = [w for w in self._doc.page_words(self.current_index)
                 if w[2] >= x0 and w[0] <= x1 and w[3] >= y0 and w[1] <= y1]
        # keep document reading order (block, line, word index)
        words.sort(key=lambda w: (w[5], w[6], w[7]))
        text = " ".join(w[4] for w in words).strip()
        # remember the selection in PDF space for annotation
        self._last_sel_page = self.current_index
        self._last_sel_rects = [tuple(w[:4]) for w in words]
        self._last_sel_text = text
        return text, QRect(start, end)

    def eventFilter(self, obj, e):
        if obj is self._label and getattr(self, "_doc", None) is not None:
            if e.type() == QEvent.Type.MouseButtonPress and e.button() == Qt.MouseButton.LeftButton:
                self._sel_start = e.position().toPoint()
                return False
            if e.type() == QEvent.Type.MouseButtonRelease and e.button() == Qt.MouseButton.LeftButton:
                if self._sel_start is not None:
                    end = e.position().toPoint()
                    drag = (abs(end.x() - self._sel_start.x())
                            + abs(end.y() - self._sel_start.y()))
                    text, rect = self._collect_selection(self._sel_start, end)
                    self._sel_start = None
                    if text and drag >= 5:  # ignore plain clicks; require a real drag
                        self._sel_overlay = list(self._last_sel_rects)
                        self._sel_overlay_page = self._last_sel_page
                        self._render()  # show the selection shadow immediately
                        self.selection_made.emit(text, rect)
                return False
            if e.type() == QEvent.Type.ContextMenu:
                self.context_requested.emit(e.globalPos())
                return True  # we show our own annotate menu
        return super().eventFilter(obj, e)
