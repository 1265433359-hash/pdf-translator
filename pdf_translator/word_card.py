from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from pdf_translator import tts


class WordCard(QFrame):
    def __init__(self, vocab, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
        self.setFrameShape(QFrame.Shape.StyledPanel); self._vocab = vocab; self._entry = None
        self.lay = QVBoxLayout(self)
        top = QHBoxLayout()
        self.word = QLabel(""); self.phon = QLabel("")
        self.say_btn = QPushButton("🔊"); self.add_btn = QPushButton("➕生词本")
        self.say_btn.clicked.connect(lambda: self._entry and tts.speak(self._entry.word))
        self.add_btn.clicked.connect(self._add)
        top.addWidget(self.word); top.addWidget(self.phon); top.addStretch()
        top.addWidget(self.say_btn); top.addWidget(self.add_btn)
        self.body = QLabel(""); self.body.setWordWrap(True)
        self.lay.addLayout(top); self.lay.addWidget(self.body); self.setMinimumWidth(340)

    def _add(self):
        if self._entry: self._vocab.add(self._entry)

    def show_entry(self, entry, global_pos):
        self._entry = entry
        self.word.setText(f"<b>{entry.word}</b>"); self.phon.setText(f"/{entry.phonetic}/" if entry.phonetic else "")
        lines = list(entry.meanings)
        if entry.collocations: lines += ["", "搭配: " + "; ".join(entry.collocations)]
        if entry.examples: lines += ["", "例句: " + " / ".join(entry.examples)]
        self.body.setText("\n".join(lines)); self.move(global_pos); self.show()
