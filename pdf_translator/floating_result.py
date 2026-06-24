"""A small floating popup that shows 划词 results near the selection.

Hosts a TranslationPane so it reuses the same multi-source rendering, but floats
above the page (no layout space) and never steals focus — reading is unaffected.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QGuiApplication

from pdf_translator.translation_pane import TranslationPane


class FloatingResult(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setObjectName("floatResult")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 8)
        bar = QHBoxLayout()
        bar.addWidget(QLabel("划词翻译"))
        bar.addStretch()
        close = QPushButton("×")
        close.setFixedSize(22, 22)
        close.setToolTip("关闭 (Esc)")
        close.clicked.connect(self.hide)
        bar.addWidget(close)
        lay.addLayout(bar)
        self.pane = TranslationPane()
        self.pane.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        lay.addWidget(self.pane)
        self.pane.content_changed.connect(self._autosize)
        self._anchor = None  # global QRect of the selected text to sit beside
        self.resize(self.MIN_W, self.MIN_H)

    MIN_W, MAX_W = 520, 680
    MIN_H, MAX_H = 150, 560

    def _autosize(self):
        """Resize to fit the content: small for a word, larger for a paragraph,
        capped (then the pane scrolls). Keep it anchored & on-screen afterwards."""
        host = self.pane.widget()
        # natural width the content would like (un-wrapped), clamped
        hint_w = host.sizeHint().width()
        w = max(self.MIN_W, min(self.MAX_W, hint_w + 44))
        self.setFixedWidth(w)
        # height for that constrained width
        inner_w = w - 44
        h = host.heightForWidth(inner_w)
        if h <= 0:
            h = host.sizeHint().height()
        total = max(self.MIN_H, min(self.MAX_H, h + 70))
        self.setMaximumHeight(self.MAX_H)
        self.resize(w, total)
        if self.isVisible():
            self._reposition()

    def _reposition(self):
        """Follow the selection but avoid the screen edges (smart placement)."""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        w, h = self.width(), self.height()
        a = self._anchor
        if a is not None:
            # prefer below the selection; if it won't fit, place above it
            x = a.left()
            if a.bottom() + 8 + h <= screen.bottom():
                y = a.bottom() + 8
            elif a.top() - 8 - h >= screen.top():
                y = a.top() - 8 - h
            else:  # neither fits cleanly -> clamp below
                y = a.bottom() + 8
        else:  # no selection rect -> top-right of the window
            parent = self.parent()
            if parent is not None and parent.isVisible():
                tr = parent.mapToGlobal(parent.rect().topRight())
                x, y = tr.x() - w - 16, tr.y() + 56
            else:
                x, y = screen.right() - w - 16, screen.top() + 60
        x = max(screen.left() + 8, min(x, screen.right() - w - 8))
        y = max(screen.top() + 8, min(y, screen.bottom() - h - 8))
        self.move(x, y)

    def show_near(self, anchor_rect=None):
        """Show the popup beside the selection (anchor_rect, global coords)."""
        self._anchor = anchor_rect if isinstance(anchor_rect, QRect) else None
        self._reposition()
        self.show()
        self.raise_()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(e)
