import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLibraryInfo, QLocale

from pdf_translator import themes, paths
from pdf_translator.app_window import MainWindow
from pdf_translator.settings import Settings


def _install_zh(app):
    """Translate Qt's standard dialog buttons (Save/Discard/OK…) to Chinese."""
    tr = QTranslator(app)
    tpath = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if tr.load(QLocale("zh_CN"), "qtbase", "_", tpath):
        app.installTranslator(tr)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF 双语翻译阅读器")
    _install_zh(app)
    icon = paths.app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    settings = Settings.load()
    themes.apply_theme(app, settings.theme)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
