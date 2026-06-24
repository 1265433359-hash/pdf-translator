from PySide6.QtWidgets import (QMainWindow, QToolBar, QFileDialog, QSpinBox, QLineEdit,
                               QMessageBox, QDockWidget, QLabel, QSplitter,
                               QProgressDialog, QComboBox)
from PySide6.QtGui import QAction, QShortcut, QKeySequence
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pdf_translator import themes
from pdf_translator.pdf_view import PdfView
from pdf_translator.pdf_document import PdfDocument
from pdf_translator.popup import TransPopup
from pdf_translator.workers import (TranslateWorker, WordLookupWorker,
                                    BatchTranslateWorker)
from pdf_translator.settings import Settings
from pdf_translator.cache import TranslationCache
from pdf_translator.engines.registry import build_engine
from pdf_translator.dictionary import Dictionary
from pdf_translator.vocabulary import Vocabulary
from pdf_translator.word_card import WordCard
from pdf_translator.translation_pane import TranslationPane
from pdf_translator.text_preprocessor import paragraphs_from_blocks
from pdf_translator.translate_queue import estimate_tokens


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器"); self.resize(1200, 800)
        self.settings = Settings.load()
        self.cache = TranslationCache()
        self.view = PdfView()
        self.pane = TranslationPane()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.pane)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.setCentralWidget(self.splitter)
        tb = QToolBar(); self.addToolBar(tb)
        tb.addAction(QAction("打开", self, triggered=self._open))
        tb.addAction(QAction("上一页", self, triggered=lambda: self.view.goto(self.view.current_index - 1)))
        tb.addAction(QAction("下一页", self, triggered=lambda: self.view.goto(self.view.current_index + 1)))
        self.page_box = QSpinBox(); self.page_box.setMinimum(1)
        self.page_box.valueChanged.connect(lambda v: self.view.goto(v - 1)); tb.addWidget(self.page_box)
        tb.addAction(QAction("放大", self, triggered=lambda: self.view.set_zoom(self.view._zoom * 1.2)))
        tb.addAction(QAction("缩小", self, triggered=lambda: self.view.set_zoom(self.view._zoom / 1.2)))
        tb.addAction(QAction("适应宽度", self, triggered=self.view.fit_width))
        tb.addAction(QAction("翻译当前页", self, triggered=self._translate_page))
        tb.addAction(QAction("翻译整篇", self, triggered=self._translate_whole))
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("搜索…")
        self.search_box.returnPressed.connect(self._search); tb.addWidget(self.search_box)

        # --- Task 7.1: view-mode toggle (双栏 / 原位替换) ---
        self.view_mode = QComboBox()
        self.view_mode.addItems(["视图：双栏", "视图：原位替换"])
        self.view_mode.currentIndexChanged.connect(self._on_view_mode_changed)
        tb.addWidget(self.view_mode)

        # --- Task 9.1: theme switcher ---
        self.theme_box = QComboBox()
        self._themes = themes.available_themes()
        for name in self._themes:
            self.theme_box.addItem(f"主题：{name}", name)
        if self.settings.theme in self._themes:
            self.theme_box.setCurrentIndex(self._themes.index(self.settings.theme))
        self.theme_box.currentIndexChanged.connect(self._on_theme_changed)
        tb.addWidget(self.theme_box)

        # --- Task 5.5: dictionary, vocabulary & word card ---
        self.dictionary = Dictionary()
        self.vocab = Vocabulary()
        self.word_card = WordCard(self.vocab)

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

    # --- Task 6.3: side-by-side page / whole-doc translation ---
    def _page_paragraphs(self, index):
        doc = self.view._doc
        if doc is None:
            return []
        return paragraphs_from_blocks(doc.page_blocks(index))

    def _all_paragraphs(self):
        doc = self.view._doc
        if doc is None:
            return []
        paras = []
        for i in range(doc.page_count):
            paras.extend(paragraphs_from_blocks(doc.page_blocks(i)))
        return paras

    def _translate_page(self):
        if self.view._doc is None:
            return
        paras = self._page_paragraphs(self.view.current_index)
        if not paras:
            self.pane.clear()
            return
        eng = self._current_engine()
        if eng is None:
            return  # dialog already shown by _current_engine
        self._batch_worker = BatchTranslateWorker(
            eng, paras, self.cache, self.settings.model,
            concurrency=self.settings.concurrency)
        self._batch_worker.done.connect(self.pane.set_paragraphs)
        self._batch_worker.failed.connect(
            lambda msg: QMessageBox.warning(self, "翻译失败", msg))
        self._batch_worker.start()

    def _translate_whole(self):
        if self.view._doc is None:
            return
        paras = self._all_paragraphs()
        if not paras:
            self.pane.clear()
            return
        eng = self._current_engine()
        if eng is None:
            return
        approx = estimate_tokens(paras)
        ans = QMessageBox.question(
            self, "翻译整篇",
            f"全文约 {len(paras)} 段，预计约 {approx} tokens。是否继续？")
        if ans != QMessageBox.StandardButton.Yes:
            return
        dlg = QProgressDialog("正在翻译整篇…", "取消", 0, len(paras), self)
        dlg.setWindowModality(Qt.WindowModality.WindowModal)
        dlg.setAutoClose(True)
        self._progress_dialog = dlg
        self._batch_worker = BatchTranslateWorker(
            eng, paras, self.cache, self.settings.model,
            concurrency=self.settings.concurrency)
        # progress is emitted from the worker thread but delivered on the GUI
        # thread via the queued signal connection below.
        self._batch_worker.progress.connect(self._on_batch_progress)
        self._batch_worker.done.connect(self._on_whole_done)
        self._batch_worker.failed.connect(self._on_batch_failed)
        self._batch_worker.start()
        dlg.show()

    def _on_batch_progress(self, done, total):
        dlg = getattr(self, "_progress_dialog", None)
        if dlg is not None:
            dlg.setValue(done)

    def _on_whole_done(self, translated):
        dlg = getattr(self, "_progress_dialog", None)
        if dlg is not None:
            dlg.setValue(dlg.maximum())
        self.pane.set_paragraphs(translated)

    def _on_batch_failed(self, msg):
        dlg = getattr(self, "_progress_dialog", None)
        if dlg is not None:
            dlg.cancel()
        QMessageBox.warning(self, "翻译失败", msg)

    # --- Task 7.1: in-place replacement view ---
    def _page_block_rects(self, index):
        """Return [(fitz.Rect, english_text)] for translatable blocks on a page."""
        import fitz
        doc = self.view._doc
        if doc is None:
            return []
        out = []
        for b in doc.page_blocks(index):
            if b[6] != 0 or not b[4].strip():
                continue
            if len(b[4].split()) <= 3:  # skip headers/footers/page numbers
                continue
            out.append((fitz.Rect(b[0], b[1], b[2], b[3]), b[4].strip()))
        return out

    def _on_view_mode_changed(self, index):
        if index == 1:
            self._render_inplace_page()
        else:
            # restore two-column: re-render the original page in the left view
            self.pane.show()
            self.view.goto(self.view.current_index)

    # --- Task 9.1: theme switching ---
    def _on_theme_changed(self, index):
        name = self.theme_box.itemData(index)
        if not name:
            return
        app = QApplication.instance()
        if app is not None:
            themes.apply_theme(app, name)
        self.settings.theme = name
        self.settings.save()

    def _render_inplace_page(self):
        if self.view._doc is None:
            self.view_mode.setCurrentIndex(0)
            return
        blocks = self._page_block_rects(self.view.current_index)
        if not blocks:
            return
        eng = self._current_engine()
        if eng is None:
            self.view_mode.setCurrentIndex(0)
            return
        rects = [r for r, _ in blocks]
        texts = [t for _, t in blocks]
        self._inplace_worker = BatchTranslateWorker(
            eng, texts, self.cache, self.settings.model,
            concurrency=self.settings.concurrency)
        self._inplace_worker.done.connect(
            lambda zh, rects=rects: self._show_inplace(rects, zh))
        self._inplace_worker.failed.connect(
            lambda msg: QMessageBox.warning(self, "翻译失败", msg))
        self._inplace_worker.start()

    def _show_inplace(self, rects, zh_list):
        from pdf_translator.inplace_renderer import render_inplace
        # Work on a throwaway copy of the page so toggling back to 双栏 is clean.
        import fitz
        src = self.view._doc._doc
        tmp = fitz.open()
        tmp.insert_pdf(src, from_page=self.view.current_index,
                       to_page=self.view.current_index)
        page = tmp[0]
        pix = render_inplace(page, list(zip(rects, zh_list)), zoom=self.view._zoom)
        self.view.show_fitz_pixmap(pix)
        self.pane.hide()

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
        # Dictionary.lookup uses a main-thread-bound sqlite connection, so it
        # MUST be called here on the GUI thread (never from a worker).
        entry = self.dictionary.lookup(word)
        if entry is None:
            # ECDICT not provisioned (or word missing): fall back to the normal
            # phrase translation popup so the app stays useful without a dict.
            eng = self._current_engine()
            if eng is None: return
            self.popup.set_loading(); self.popup.show_at(self.cursor().pos())
            self._worker = TranslateWorker(eng, word, self.cache, self.settings.model)
            self._worker.chunk.connect(self.popup.append_chunk)
            self._worker.failed.connect(self.popup.set_error)
            self._worker.start()
            return

        # Instant base info from ECDICT.
        self.word_card.show_entry(entry, self.cursor().pos())

        # Enrich collocations/examples asynchronously via the engine (network).
        # Enrich only if a key is configured; never pop a dialog from the
        # best-effort enrich path (offline ECDICT-only use must stay silent).
        if not self.settings.get_api_key(self.settings.engine):
            return
        eng = self._current_engine()
        if eng is None: return
        self._enrich_worker = WordLookupWorker(eng, word)
        self._enrich_worker.found.connect(
            lambda enriched, base=entry: self._merge_word_entry(base, enriched))
        self._enrich_worker.start()

    def _merge_word_entry(self, base, enriched):
        # Merge engine-supplied collocations/examples into the displayed entry
        # and refresh the card (entry may already be dismissed).
        if not self.word_card.isVisible(): return
        if enriched.collocations:
            base.collocations = enriched.collocations
        if enriched.examples:
            base.examples = enriched.examples
        self.word_card.show_entry(base, self.word_card.pos())

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
