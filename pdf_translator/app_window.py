from PySide6.QtWidgets import QMainWindow, QToolBar, QFileDialog, QSpinBox
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

    def _open(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开 PDF", "", "PDF (*.pdf)")
        if path:
            doc = PdfDocument.open(path)
            self.view.load(doc); self.page_box.setMaximum(doc.page_count)
