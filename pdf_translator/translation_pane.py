from PySide6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class TranslationPane(QScrollArea):
    def __init__(self):
        super().__init__()
        self._host = QWidget()
        self._lay = QVBoxLayout(self._host)
        self._lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._host)
        self.setWidgetResizable(True)

    def clear(self):
        while self._lay.count():
            w = self._lay.takeAt(0).widget()
            if w:
                w.deleteLater()

    def set_paragraphs(self, paras):
        self.clear()
        for p in paras:
            lab = QLabel(p)
            lab.setWordWrap(True)
            lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._lay.addWidget(lab)
