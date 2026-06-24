import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from pdf_translator.app_window import MainWindow


class FakeEngine:
    def __init__(self, chunks):
        self._chunks = chunks
    def translate_stream(self, text):
        for c in self._chunks:
            yield c


def run():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()

    fake = FakeEngine(["你好", "，", "世界"])
    w._current_engine = lambda: fake
    # avoid sqlite cache interfering with the assertion
    w.cache = None

    # --- phrase path ---
    w._pending = "hello world"
    w._translate_pending()
    w._worker.wait(5000)
    app.processEvents()
    body = w.popup.body.text()
    assert body == "你好，世界", f"phrase body was {body!r}"
    print("PHRASE OK:", body)

    # --- pin to dock ---
    w.popup.pin_btn.setChecked(True)
    app.processEvents()
    assert w._dock is not None, "dock not created on pin"
    assert not w.popup.isVisible(), "popup should hide when pinned"
    assert w._dock_label.text() == "你好，世界", w._dock_label.text()
    print("PIN OK:", w._dock_label.text())

    # --- single-word path routes through popup (no crash) ---
    w.popup.pin_btn.setChecked(False)
    app.processEvents()
    w.popup.body.setText("")
    fake2 = FakeEngine(["苹果"])
    w._current_engine = lambda: fake2
    w._pending = "apple"
    w._translate_pending()
    w._worker.wait(5000)
    app.processEvents()
    wb = w.popup.body.text()
    assert wb == "苹果", f"word body was {wb!r}"
    print("WORD OK:", wb)

    print("SMOKE PASS")


if __name__ == "__main__":
    run()
