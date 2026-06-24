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
        lay.addWidget(self.pane)
        self.resize(440, 340)

    def show_near(self, global_pos):
        """Show near a global point, kept fully on screen."""
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = min(global_pos.x() + 14, screen.right() - self.width() - 8)
        y = min(global_pos.y() + 14, screen.bottom() - self.height() - 8)
        x = max(screen.left() + 8, x)
        y = max(screen.top() + 8, y)
        self.move(x, y)
        self.show()
        self.raise_()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(e)
