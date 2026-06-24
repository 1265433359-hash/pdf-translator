"""In-app vocabulary book: browse / search / delete / speak / export saved words."""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
                               QTableWidget, QTableWidgetItem, QPushButton,
                               QHeaderView, QAbstractItemView, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt


class VocabularyDialog(QDialog):
    def __init__(self, vocab, on_speak=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("生词本")
        self.resize(680, 480)
        self.vocab = vocab
        self._on_speak = on_speak

        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("搜索单词 / 释义…")
        self.search.textChanged.connect(self._reload)
        self.count_label = QLabel("")
        top.addWidget(self.search, 1)
        top.addWidget(self.count_label)
        root.addLayout(top)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["单词", "音标", "释义", "来源"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSortingEnabled(True)
        root.addWidget(self.table)

        bar = QHBoxLayout()
        speak_btn = QPushButton("🔊 朗读")
        speak_btn.clicked.connect(self._speak)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._delete)
        export_btn = QPushButton("导出 Anki")
        export_btn.clicked.connect(self._export)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        bar.addWidget(speak_btn)
        bar.addWidget(del_btn)
        bar.addStretch()
        bar.addWidget(export_btn)
        bar.addWidget(close_btn)
        root.addLayout(bar)

        self._reload()

    def _reload(self, *_):
        q = self.search.text().strip().lower()
        rows = self.vocab.all()
        if q:
            rows = [r for r in rows
                    if q in r["word"].lower()
                    or any(q in m.lower() for m in r["meanings"])]
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["word"]))
            self.table.setItem(i, 1, QTableWidgetItem(r.get("phonetic", "")))
            self.table.setItem(i, 2, QTableWidgetItem(" ".join(r["meanings"])))
            self.table.setItem(i, 3, QTableWidgetItem(r.get("source", "")))
        self.table.setSortingEnabled(True)
        self.count_label.setText(f"共 {self.vocab.count()} 个")

    def _selected_words(self):
        words = []
        for idx in self.table.selectionModel().selectedRows():
            item = self.table.item(idx.row(), 0)
            if item:
                words.append(item.text())
        return words

    def _speak(self):
        words = self._selected_words()
        if words and self._on_speak:
            self._on_speak(words[0])

    def _delete(self):
        words = self._selected_words()
        if not words:
            return
        for w in words:
            self.vocab.remove(w)
        self._reload()

    def _export(self):
        from pdf_translator.anki_export import export_csv
        rows = self.vocab.all()
        if not rows:
            QMessageBox.information(self, "生词本为空", "还没有收藏单词。")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 Anki", "vocab.txt",
                                              "Text (*.txt)")
        if path:
            export_csv(rows, path)
            QMessageBox.information(self, "已导出", f"已导出 {len(rows)} 个单词到：\n{path}")
