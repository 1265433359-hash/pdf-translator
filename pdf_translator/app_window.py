from PySide6.QtWidgets import (QMainWindow, QToolBar, QFileDialog, QSpinBox, QLineEdit,
                               QMessageBox, QDockWidget, QLabel, QSplitter,
                               QProgressDialog, QComboBox, QToolButton, QMenu,
                               QStackedWidget, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                               QWidget)
from PySide6.QtGui import QAction, QShortcut, QKeySequence, QCursor
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
from pdf_translator.glossary import Glossary
from pdf_translator.vocabulary import Vocabulary
from pdf_translator.word_card import WordCard
from pdf_translator.translation_pane import TranslationPane
from pdf_translator.floating_result import FloatingResult
from pdf_translator.home import HomeWidget
from pdf_translator.text_preprocessor import paragraphs_from_blocks
from pdf_translator.translate_queue import estimate_tokens


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器")
        self.settings = Settings.load()
        self.resize(self.settings.win_w, self.settings.win_h)
        if self.settings.win_max:
            self.setWindowState(Qt.WindowState.WindowMaximized)
        self._current_path = None
        if self.settings.engine == "youdao":  # 有道 is now a separate source, not an LLM engine
            self.settings.engine = "deepseek"
        self.cache = TranslationCache()
        self.glossary = Glossary()
        self.view = PdfView()
        # 划词结果显示在浮窗(不再占用右栏);PDF 占满整个阅读区
        self.result = FloatingResult(self)
        self.pane = self.result.pane  # reuse the same multi-source rendering API
        # home page (launcher) + reader, swapped via a stack
        self.home = HomeWidget()
        self.home.open_requested.connect(self._open)
        self.home.open_path_requested.connect(self._open_path)
        self.home.clear_requested.connect(self._clear_recents)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.home)   # index 0
        self.stack.addWidget(self.view)   # index 1 — full-width PDF
        self.setCentralWidget(self.stack)
        # outline / bookmarks dock (hidden until a PDF with a TOC is opened)
        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemClicked.connect(self._on_outline_clicked)
        self.outline_dock = QDockWidget("目录", self)
        self.outline_dock.setWidget(self.outline_tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.outline_dock)
        self.outline_dock.hide()
        # --- left navigation sidebar (primary actions) ---
        side = QToolBar("导航"); side.setObjectName("sidebar")
        side.setMovable(False)
        side.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, side)
        self.nav_home = QAction("🏠  首页", self, checkable=True, triggered=self._go_home)
        self.nav_open = QAction("📂  打开", self, triggered=self._open)
        self.nav_outline = QAction("🔖  目录", self, checkable=True, triggered=self._toggle_outline)
        self.nav_vocab = QAction("📒  生词本", self, triggered=self._open_vocab)
        self.settings_action = QAction("⚙  设置", self, triggered=self._open_settings)
        for a in (self.nav_home, self.nav_open, self.nav_outline, self.nav_vocab):
            side.addAction(a)
        spacer = QWidget(); spacer.setSizePolicy(QSizePolicy.Policy.Preferred,
                                                 QSizePolicy.Policy.Expanding)
        side.addWidget(spacer)
        side.addAction(self.settings_action)

        # --- top reading toolbar ---
        tb = QToolBar("阅读"); tb.setMovable(False); self.addToolBar(tb)
        tb.addAction(QAction("◀ 上一页", self, triggered=lambda: self.view.goto(self.view.current_index - 1)))
        tb.addAction(QAction("下一页 ▶", self, triggered=lambda: self.view.goto(self.view.current_index + 1)))
        self.page_box = QSpinBox(); self.page_box.setMinimum(1)
        self.page_box.valueChanged.connect(lambda v: self.view.goto(v - 1)); tb.addWidget(self.page_box)
        tb.addSeparator()
        tb.addAction(QAction("＋ 放大", self, triggered=lambda: self.view.set_zoom(self.view._zoom * 1.2)))
        tb.addAction(QAction("－ 缩小", self, triggered=lambda: self.view.set_zoom(self.view._zoom / 1.2)))
        tb.addAction(QAction("适应宽度", self, triggered=self.view.fit_width))
        tb.addSeparator()
        # annotation mode + undo/save
        self.annot_mode = QComboBox()
        self.annot_mode.addItems(["划词翻译", "高亮", "删除线"])
        self.annot_mode.setToolTip("拖选文字时执行的动作；右键选区也可随时选高亮/删除线")
        tb.addWidget(self.annot_mode)
        tb.addAction(QAction("撤销标注", self, triggered=self._undo_annotation))
        tb.addAction(QAction("保存标注", self, triggered=self._save_annotations))
        self._annot_dirty = False
        spacer2 = QWidget(); spacer2.setSizePolicy(QSizePolicy.Policy.Expanding,
                                                   QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer2)
        self.search_box = QLineEdit(); self.search_box.setPlaceholderText("在文档中搜索…")
        self.search_box.setMaximumWidth(220)
        self.search_box.returnPressed.connect(self._search); tb.addWidget(self.search_box)
        self._themes = themes.available_themes()
        self._refresh_recents_menu()

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
        self.view.page_changed.connect(self._on_page_changed)
        self.view.context_requested.connect(self._show_annot_menu)
        self.view.cleared.connect(self.result.hide)  # click elsewhere -> close popup
        sc = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        sc.activated.connect(self._translate_pending)
        self.nav_home.setChecked(True)  # start on the home page

    def _on_page_changed(self, index):
        """Keep the toolbar page box in sync; remember the reading position."""
        self.page_box.blockSignals(True)
        self.page_box.setValue(index + 1)
        self.page_box.blockSignals(False)
        if self._current_path:
            from pdf_translator import recents
            recents.set_page(self._current_path, index)

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF (*.pdf)")
        if path:
            self._open_path(path)

    def _go_home(self):
        self._refresh_recents_menu()
        self.stack.setCurrentIndex(0)
        self.nav_home.setChecked(True)

    def _open_path(self, path):
        import os
        from pdf_translator import recents
        if not os.path.exists(path):
            QMessageBox.warning(self, "文件不存在", f"找不到文件：\n{path}")
            recents.remove_recent(path)
            self._refresh_recents_menu()
            return
        saved_page = recents.page_for(path)   # before add_recent
        doc = PdfDocument.open(path)
        self.view.load(doc)
        self.page_box.setMaximum(doc.page_count)
        self.stack.setCurrentIndex(1)   # switch to the reader
        self.nav_home.setChecked(False)
        self.view.fit_width()  # auto-fit the left pane to the opened article
        self._current_path = path
        self._populate_outline(doc.get_toc())
        if 0 < saved_page < doc.page_count:
            self.view.goto(saved_page)    # resume where you left off
        recents.add_recent(path)
        self._refresh_recents_menu()
        self.setWindowTitle(f"{os.path.basename(path)} — PDF 双语翻译阅读器")
        if not doc.has_text_layer():
            QMessageBox.warning(self, "无法翻译",
                "此 PDF 没有可提取的文字（疑似扫描件），暂不支持翻译。OCR 将在后续版本支持。")

    def _refresh_recents_menu(self):
        """Recents now live on the home page (sidebar 首页)."""
        from pdf_translator import recents
        self.home.set_recents(recents.all_recents())

    def _clear_recents(self):
        from pdf_translator import recents
        recents.clear()
        self._refresh_recents_menu()

    def _export_vocab(self):
        from pdf_translator.anki_export import export_csv
        rows = self.vocab.all()
        if not rows:
            QMessageBox.information(self, "生词本为空", "当前生词本没有可导出的单词。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 Anki", "anki.txt", "文本 (*.txt)")
        if not path:
            return
        export_csv(rows, path)
        QMessageBox.information(self, "导出完成", f"已导出 {len(rows)} 个单词到\n{path}")

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

    def _worker_busy(self, attr):
        """True if the named worker exists and is still running."""
        w = getattr(self, attr, None)
        return w is not None and w.isRunning()

    def _translate_page(self):
        if self.view._doc is None:
            return
        if self._worker_busy("_batch_worker"):
            return  # ignore re-trigger while a batch is in flight
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
        if self._worker_busy("_batch_worker"):
            return  # ignore re-trigger while a batch is in flight
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
        # NOTE: the "取消" button is cosmetic — it dismisses the dialog but does
        # NOT interrupt the running thread pool (a real cancel flag is out of
        # scope here). The worker finishes its batch regardless.
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

    def _render_inplace_page(self):
        if self.view._doc is None:
            self.view_mode.setCurrentIndex(0)
            return
        if self._worker_busy("_inplace_worker"):
            return  # ignore re-trigger while an in-place render is in flight
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
        # Drag-select action depends on the toolbar mode.
        self._pending = text
        mode = self.annot_mode.currentText()
        if mode == "高亮":
            self._annotate("highlight")
        elif mode == "删除线":
            self._annotate("strikeout")
        else:  # 划词翻译:松手即译(空格仍可作为补充触发)
            self._translate_pending()

    def _annotate(self, kind):
        if self.view.annotate_selection(kind):
            self._annot_dirty = True

    def _undo_annotation(self):
        if self.view.undo_last_annotation():
            self._annot_dirty = True

    def _show_annot_menu(self, global_pos):
        """Right-click menu on a selection: highlight / strikeout / copy.
        (翻译 omitted — selection auto-translates already.)"""
        text, page, rects = self.view.last_selection()
        if not rects:
            return
        menu = QMenu(self)
        menu.addAction("高亮", lambda: self._annotate("highlight"))
        menu.addAction("删除线", lambda: self._annotate("strikeout"))
        menu.addAction("复制", lambda: QApplication.clipboard().setText(text))
        menu.exec(global_pos)

    def _save_annotations(self):
        doc = self.view._doc
        if doc is None:
            QMessageBox.information(self, "无文件", "请先打开一个 PDF。")
            return
        try:
            doc.save()
            self._annot_dirty = False
            QMessageBox.information(self, "已保存", "标注已写入 PDF 文件。")
        except Exception as e:
            QMessageBox.warning(self, "保存失败",
                f"无法写入该 PDF：\n{e}\n\n（文件可能被占用或只读）")

    def _populate_outline(self, toc):
        """Build the outline tree from PyMuPDF TOC entries [level, title, page]."""
        self.outline_tree.clear()
        if not toc:
            self.outline_dock.hide()
            self.nav_outline.setChecked(False)
            return
        stack = []  # (level, item)
        for level, title, page in toc:
            item = QTreeWidgetItem([title.strip() or "(无标题)"])
            item.setData(0, Qt.ItemDataRole.UserRole, page)
            while stack and stack[-1][0] >= level:
                stack.pop()
            if stack:
                stack[-1][1].addChild(item)
            else:
                self.outline_tree.addTopLevelItem(item)
            stack.append((level, item))
        self.outline_tree.expandToDepth(0)
        self.outline_dock.show()  # auto-reveal when the PDF has bookmarks
        self.nav_outline.setChecked(True)

    def _on_outline_clicked(self, item, _col):
        page = item.data(0, Qt.ItemDataRole.UserRole)
        if page:
            self.view.goto(int(page) - 1)  # TOC pages are 1-based

    def _toggle_outline(self):
        vis = not self.outline_dock.isVisible()
        self.outline_dock.setVisible(vis)
        self.nav_outline.setChecked(vis)

    def _open_vocab(self):
        from pdf_translator.vocab_dialog import VocabularyDialog
        VocabularyDialog(self.vocab, on_speak=self._speak, parent=self).exec()

    def _save_window_state(self):
        self.settings.win_max = self.isMaximized()
        if not self.isMaximized():
            self.settings.win_w = self.width()
            self.settings.win_h = self.height()
        self.settings.save()

    def closeEvent(self, e):
        """Save window state; ask to save annotations if there are unsaved ones."""
        self._save_window_state()
        if getattr(self, "_annot_dirty", False) and self.view._doc is not None:
            box = QMessageBox(self)
            box.setWindowTitle("保存标注")
            box.setIcon(QMessageBox.Icon.Question)
            box.setText("有未保存的标注，要写入 PDF 吗？")
            save_btn = box.addButton("保存", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("不保存", QMessageBox.ButtonRole.DestructiveRole)
            cancel_btn = box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            clicked = box.clickedButton()
            if clicked is cancel_btn:
                e.ignore(); return
            if clicked is save_btn:
                try:
                    self.view._doc.save()
                except Exception as ex:
                    QMessageBox.warning(self, "保存失败", f"无法写入：\n{ex}")
                    e.ignore(); return
        e.accept()

    def _open_settings(self):
        from pdf_translator.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self.settings, self.cache,
                             glossary=self.glossary, parent=self)
        if dlg.exec():
            # settings (engine/model/keys/concurrency/prompt/theme) are persisted by
            # the dialog; re-apply the possibly-changed theme.
            app = QApplication.instance()
            if app is not None:
                themes.apply_theme(app, self.settings.theme)

    def _current_engine(self):
        key = self.settings.get_api_key(self.settings.engine)
        if not key:
            QMessageBox.information(self, "需要 API Key",
                "请先在「设置」中为当前引擎填写 API Key。")
            return None
        app_secret = None
        if self.settings.engine == "youdao":
            app_secret = self.settings.get_api_key("youdao_secret")
        # Reuse the engine (and its httpx connection pool) across translations
        # so we don't re-do the TLS handshake every time — major latency win.
        sig = (self.settings.engine, self.settings.model, key, app_secret,
               self.settings.custom_base_url, self.settings.prompt)
        if getattr(self, "_engine_sig", None) == sig and getattr(self, "_engine_cached", None):
            return self._engine_cached
        self._engine_cached = build_engine(
            self.settings.engine, key,
            self.settings.model or None,
            prompt=self.settings.prompt or None,
            base_url=self.settings.custom_base_url or None,
            app_secret=app_secret,
            glossary=self.glossary)
        self._engine_sig = sig
        return self._engine_cached

    def _speak(self, word):
        from pdf_translator import tts
        tts.speak(word)

    def _translate_pending(self):
        if not getattr(self, "_pending", None): return
        if self._worker_busy("_worker"): return  # ignore rapid re-trigger
        from pdf_translator.textutil import is_single_word
        if is_single_word(self._pending):
            self._show_word_card(self._pending); return
        self._translate_phrase(self._pending)

    def _youdao_engine(self):
        ak = self.settings.get_api_key("youdao")
        sk = self.settings.get_api_key("youdao_secret")
        if not ak or not sk:
            return None
        from pdf_translator.engines.youdao import YoudaoEngine
        return YoudaoEngine(ak, sk)

    def _translate_phrase(self, text):
        """Show every enabled translation source for a phrase (有道 / 大模型)."""
        from pdf_translator.workers import CallWorker
        yeng = self._youdao_engine() if self.settings.use_youdao else None
        youdao_unconfigured = self.settings.use_youdao and yeng is None
        want_youdao = self.settings.use_youdao  # show the section either way
        want_llm = self.settings.use_llm
        if not want_youdao and not want_llm:
            self.pane.show_error("未启用任何翻译来源：请在「设置」勾选 大模型 或 有道词典。")
            self.result.show_near(self.view.selection_global_rect())
            return
        self.pane.start_sources(text, youdao=want_youdao, llm=want_llm)
        self.result.show_near(self.view.selection_global_rect())
        if want_youdao:
            if youdao_unconfigured:
                self.pane.set_youdao("（有道未配置 appKey/appSecret，请在设置填写）")
            else:
                self._quick_worker = CallWorker(lambda: yeng.translate(text))
                self._quick_worker.ok.connect(self.pane.set_youdao)
                self._quick_worker.failed.connect(
                    lambda e: self.pane.set_youdao(f"（有道失败：{e[:50]}）"))
                self._quick_worker.start()
        if want_llm:
            eng = self._current_engine()
            if eng is None:
                return  # _current_engine showed the API-key dialog
            self._worker = TranslateWorker(eng, text, self.cache, self.settings.model)
            self._worker.chunk.connect(self.pane.append_translation)
            self._worker.failed.connect(self.pane.main_error)
            self._worker.start()

    def _show_word_card(self, word):
        # Dictionary.lookup uses a main-thread-bound sqlite connection, so it
        # MUST be called here on the GUI thread (never from a worker).
        entry = self.dictionary.lookup(word)
        if entry is None:
            # no offline dict entry -> use the enabled phrase sources (有道/大模型)
            self._translate_phrase(word)
            return

        # Offline dictionary (ECDICT) base info, shown in the floating popup.
        self._render_word_card(entry)
        self.result.show_near(self.view.selection_global_rect())

        # Enrich collocations/examples via the LLM only if 大模型 is enabled and
        # a key is configured; never pop a dialog from this best-effort path.
        if not self.settings.use_llm:
            return
        if not self.settings.get_api_key(self.settings.engine):
            return
        eng = self._current_engine()
        if eng is None: return
        self._enrich_worker = WordLookupWorker(eng, word)
        self._enrich_worker.found.connect(
            lambda enriched, base=entry: self._merge_word_entry(base, enriched))
        self._enrich_worker.start()

    def _render_word_card(self, entry):
        """(Re)render the word card with current vocab state (saved / forgot count)."""
        saved = self.vocab.is_saved(entry.word)
        forgot = self.vocab.forgot_count(entry.word) if saved else 0
        self.pane.show_word(
            entry, on_speak=self._speak,
            on_add=lambda e: (self.vocab.add(e), self._render_word_card(e)),
            on_forgot=lambda w, e=entry: (self.vocab.increment_forgot(w),
                                          self._render_word_card(e)),
            is_saved=saved, forgot_count=forgot)

    def _merge_word_entry(self, base, enriched):
        # Merge engine-supplied collocations/examples into the displayed entry
        # and refresh the card (preserving saved/forgot state).
        if enriched.collocations:
            base.collocations = enriched.collocations
        if enriched.examples:
            base.examples = enriched.examples
        self._render_word_card(base)

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
