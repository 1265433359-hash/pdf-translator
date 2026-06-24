from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 双语翻译阅读器")
        self.resize(1200, 800)
        tb = QToolBar()
        self.addToolBar(tb)
        self.setCentralWidget(QLabel("打开一个 PDF 开始"))
