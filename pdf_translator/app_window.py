from PySide6.QtWidgets import (QMainWindow, QToolBar, QFileDialog, QSpinBox, QLineEdit,
                               QMessageBox, QDockWidget, QLabel)
from PySide6.QtGui import QAction, QShortcut, QKeySequence
from PySide6.QtCore import Qt
from pdf_translator.pdf_view import PdfView
from pdf_translator.pdf_document import PdfDocument
from pdf_translator.popup import TransPopup
from pdf_translator.workers import TranslateWorker
from pdf_translator.settings import Settings
from pdf_translator.cache import TranslationCache
from pdf_translator.engines.registry import build_engine


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器"); self.resize(1200, 800)
        self.settings = Settings.load()
        self.cache = TranslationCache()
        self.view = PdfView(); self.setCentralWidget(self.view)
        tb = QToolBar(); self.addToolBar(tb)
        tb.addAction(QAction("打开", self, triggered=self._open))
        tb.addAction(QAction("上一页", self, triggered=lambda: self.view.goto(self.view.current_index - 1)))
        tb.addAction(QAction("下一页", self, triggered=lambda: self.view.goto(self.view.current_index + 1)))
        self.page_box = QSpinBox(); self.page_box.setMinimum(1)
        self.page_box.valueChanged.connect(lambda v: self.view.goto(v - 1)); tb.addWidget(self.page_box)
        tb.addAction(QAction("放大", self, triggered=lambda: self.view.set_zoom(self.view._zoom * 1.2)))
        tb.addAction(QAction("缩小", self, triggered=lambda: self.view.set_zoom(self.view._zoom / 1.2)))
        tb.addAction(QAction("适应宽度", self, triggered=self.view.fit_width))
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("搜索…")
        self.search_box.returnPressed.connect(self._search); tb.addWidget(self.search_box)

        # --- Task 4.3: selection-triggered translation popup ---
        self._pending = None
        self.popup = TransPopup(self)
        self.popup.pin_toggled.connect(self._on_pin_toggled)
        self._dock = None
        self.view.selection_made.connect(self._on_selection)
        sc = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        sc.activated.connect(self._translate_pending)

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF (*.pdf)")
        if path:
            doc = PdfDocument.open(path)
            self.view.load(doc); self.page_box.setMaximum(doc.page_count)
            if not doc.has_text_layer():
                QMessageBox.warning(self, "无法翻译",
                    "此 PDF 没有可提取的文字（疑似扫描件），暂不支持翻译。OCR 将在后续版本支持。")

    def _search(self):
        q = self.search_box.text().strip()
        if not q or not self.view._doc: return
        hits = self.view._doc.search(q)
        if hits: self.view.highlight(hits[0][0], [r for i, r in hits if i == hits[0][0]])

    # --- Task 4.3 ---
    def _on_selection(self, text, rect):
        self._pending = text

    def _current_engine(self):
        key = self.settings.get_api_key(self.settings.engine)
        if not key:
            QMessageBox.information(self, "需要 API Key",
                "请先在「设置」中为当前引擎填写 API Key。")
            return None
        return build_engine(self.settings.engine, key,
                            self.settings.model or None,
                            base_url=self.settings.custom_base_url or None)

    def _translate_pending(self):
        if not getattr(self, "_pending", None): return
        from pdf_translator.textutil import is_single_word
        if is_single_word(self._pending):
            self._show_word_card(self._pending); return
        eng = self._current_engine()
        if eng is None: return
        self.popup.set_loading(); self.popup.show_at(self.cursor().pos())
        self._worker = TranslateWorker(eng, self._pending, self.cache, self.settings.model)
        self._worker.chunk.connect(self.popup.append_chunk)
        self._worker.failed.connect(self.popup.set_error)
        self._worker.start()

    def _show_word_card(self, word):
        # TODO Phase 5: replace with WordCard dictionary card
        eng = self._current_engine()
        if eng is None: return
        self.popup.set_loading(); self.popup.show_at(self.cursor().pos())
        self._worker = TranslateWorker(eng, word, self.cache, self.settings.model)
        self._worker.chunk.connect(self.popup.append_chunk)
        self._worker.failed.connect(self.popup.set_error)
        self._worker.start()

    def _on_pin_toggled(self, pinned):
        if pinned:
            if self._dock is None:
                self._dock = QDockWidget("译文", self)
                self._dock_label = QLabel(""); self._dock_label.setWordWrap(True)
                self._dock_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                self._dock_label.setAlignment(Qt.AlignmentFlag.AlignTop)
                self._dock.setWidget(self._dock_label)
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._dock)
            self._dock_label.setText(self.popup.body.text())
            self._dock.show()
            self.popup.hide()
        else:
            if self._dock is not None:
                self.popup.body.setText(self._dock_label.text())
                self._dock.hide()
                self.popup.show_at(self.cursor().pos())
