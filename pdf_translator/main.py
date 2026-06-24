import sys

from PySide6.QtWidgets import QApplication

from pdf_translator import themes
from pdf_translator.app_window import MainWindow
from pdf_translator.settings import Settings


def main():
    app = QApplication(sys.argv)
    settings = Settings.load()
    themes.apply_theme(app, settings.theme)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
