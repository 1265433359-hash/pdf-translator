from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal


class TransPopup(QFrame):
    pin_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(self)
        bar = QHBoxLayout()
        self.copy_btn = QPushButton("复制"); self.pin_btn = QPushButton("📌")
        self.pin_btn.setCheckable(True)
        self.pin_btn.toggled.connect(self.pin_toggled.emit)
        bar.addWidget(self.copy_btn); bar.addWidget(self.pin_btn); bar.addStretch()
        self.body = QLabel(""); self.body.setWordWrap(True); self.body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addLayout(bar); lay.addWidget(self.body)
        self.setMinimumWidth(320)
        from PySide6.QtWidgets import QApplication
        self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.body.text()))

    def show_at(self, global_pos): self.move(global_pos); self.show()

    def set_loading(self): self.body.setText("翻译中…")

    def append_chunk(self, s):
        if self.body.text() == "翻译中…": self.body.setText("")
        self.body.setText(self.body.text() + s)

    def set_error(self, s): self.body.setText("⚠ " + s)
