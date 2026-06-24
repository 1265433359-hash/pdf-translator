"""A small floating popup that shows 划词 results near the selection.

Hosts a TranslationPane so it reuses the same multi-source rendering, but floats
above the page (no layout space) and never steals focus — reading is unaffected.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
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
        self.resize(self.MIN_W, self.MIN_H)

    MIN_W, MAX_W = 280, 560
    MIN_H, MAX_H = 90, 540

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
        """Anchor to the top-right of the main window, always fully on screen."""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        parent = self.parent()
        if parent is not None and parent.isVisible():
            tr = parent.mapToGlobal(parent.rect().topRight())
            x = tr.x() - self.width() - 16
            y = tr.y() + 56  # just below the toolbar
        else:
            x = screen.right() - self.width() - 16
            y = screen.top() + 60
        x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
        y = max(screen.top() + 8, min(y, screen.bottom() - self.height() - 8))
        self.move(x, y)

    def show_near(self, global_pos=None):
        """Show the popup at a fixed, always-visible spot (top-right of the window)."""
        self._reposition()
        self.show()
        self.raise_()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(e)
