from PySide6.QtWidgets import (QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QPushButton)
from PySide6.QtCore import Qt, Signal


class TranslationPane(QScrollArea):
    """Right column: shows page translation, or a 划词 explanation (word/phrase)."""

    content_changed = Signal()  # emitted whenever shown content changes (for autosize)

    def __init__(self):
        super().__init__()
        self._host = QWidget()
        self._lay = QVBoxLayout(self._host)
        self._lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self._host)
        self.setWidgetResizable(True)
        self._stream_label = None
        self._quick_label = None

    def clear(self):
        self._stream_label = None
        self._quick_label = None
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            else:
                lay = item.layout()
                if lay:
                    while lay.count():
                        cw = lay.takeAt(0).widget()
                        if cw:
                            cw.deleteLater()

    def set_paragraphs(self, paras):
        self.clear()
        for p in paras:
            self._lay.addWidget(self._wrap_label(p))
        self.content_changed.emit()

    # --- 划词 explanation -------------------------------------------------
    def show_word(self, entry, on_speak=None, on_add=None, on_forgot=None,
                  is_saved=False, forgot_count=0):
        """Dictionary entry + vocab controls. When already saved, the add button
        becomes a disabled '✓ 已加入生词本' and a '不记得 (N)' button appears."""
        self.clear()
        header = QHBoxLayout()
        title = QLabel(f"<b>{entry.word}</b>")
        phon = QLabel(f"/{entry.phonetic}/" if entry.phonetic else "")
        header.addWidget(title)
        header.addWidget(phon)
        header.addStretch()
        if on_speak:
            b = QPushButton("🔊"); b.setFixedWidth(36); b.setToolTip("播放")
            b.clicked.connect(lambda: on_speak(entry.word)); header.addWidget(b)
        if is_saved:
            added = QPushButton("✓ 已加入生词本"); added.setEnabled(False)
            header.addWidget(added)
            if on_forgot:
                fb = QPushButton(f"不记得 ({forgot_count})")
                fb.setToolTip("点一下,后台记一次没记住,用于按遗忘度排序复习")
                fb.clicked.connect(lambda: on_forgot(entry.word))
                header.addWidget(fb)
        elif on_add:
            b = QPushButton("➕ 生词本")
            b.clicked.connect(lambda: on_add(entry)); header.addWidget(b)
        self._lay.addLayout(header)

        lines = list(entry.meanings)
        if entry.collocations:
            lines += ["", "搭配：" + "；".join(entry.collocations)]
        if entry.examples:
            lines += ["", "例句：" + " / ".join(entry.examples)]
        self._lay.addWidget(self._wrap_label("\n".join(lines)))
        self.content_changed.emit()

    # --- streaming phrase translation ------------------------------------
    def show_translation_start(self, source_text="", title="译文"):
        self.clear()
        if source_text:
            self._lay.addWidget(self._wrap_label("【原文】"))
            src = self._wrap_label(source_text)
            src.setStyleSheet("color: gray;")
            self._lay.addWidget(src)
        self._lay.addWidget(self._wrap_label(f"【{title}】"))
        self._stream_label = self._wrap_label("翻译中…")
        self._lay.addWidget(self._stream_label)
        self.content_changed.emit()

    def append_translation(self, chunk):
        if self._stream_label is None:
            self.show_translation_start()
        if self._stream_label.text() == "翻译中…":
            self._stream_label.setText("")
        self._stream_label.setText(self._stream_label.text() + chunk)
        self.content_changed.emit()

    # --- multi-source: 有道词典 / 大模型, each independently shown -----------
    def start_sources(self, source_text="", youdao=False, llm=False):
        self.clear()
        if source_text:
            self._lay.addWidget(self._wrap_label("【原文】"))
            s = self._wrap_label(source_text)
            s.setStyleSheet("color: gray;")
            self._lay.addWidget(s)
        if youdao:
            self._lay.addWidget(self._wrap_label("【有道词典】"))
            self._quick_label = self._wrap_label("…")
            self._lay.addWidget(self._quick_label)
        if llm:
            self._lay.addWidget(self._wrap_label("【大模型】"))
            self._stream_label = self._wrap_label("翻译中…")
            self._lay.addWidget(self._stream_label)
        self.content_changed.emit()

    def set_youdao(self, text):
        if self._quick_label is not None:
            self._quick_label.setText(text)
        self.content_changed.emit()

    def main_error(self, msg):
        if self._stream_label is not None:
            self._stream_label.setText("⚠ " + msg)
            self.content_changed.emit()
        else:
            self.show_error(msg)

    def show_error(self, msg):
        self.clear()
        self._lay.addWidget(self._wrap_label("⚠ " + msg))
        self.content_changed.emit()

    def current_text(self):
        """All label text currently shown (for tests / introspection)."""
        parts = []
        for i in range(self._lay.count()):
            w = self._lay.itemAt(i).widget()
            if isinstance(w, QLabel):
                parts.append(w.text())
        return "\n".join(parts)

    def stream_text(self):
        return self._stream_label.text() if self._stream_label is not None else ""

    @staticmethod
    def _wrap_label(text):
        lab = QLabel(text)
        lab.setWordWrap(True)
        lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        return lab
