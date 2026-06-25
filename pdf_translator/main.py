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


def _set_windows_app_id():
    """Give Windows a distinct AppUserModelID so the taskbar uses OUR window icon
    instead of pythonw.exe's. Must run before any window is created."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "pdftranslator.reader")
        except Exception:
            pass


def main():
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("PDF 双语翻译阅读器")
    _install_zh(app)
    icon = paths.app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    settings = Settings.load()
    themes.apply_theme(app, settings.theme)
    win = MainWindow()
    if icon is not None:
        win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
