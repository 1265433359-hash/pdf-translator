from PySide6.QtWidgets import QMainWindow, QToolBar, QFileDialog, QSpinBox, QLineEdit, QMessageBox
from PySide6.QtGui import QAction
from pdf_translator.pdf_view import PdfView
from pdf_translator.pdf_document import PdfDocument


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器"); self.resize(1200, 800)
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
