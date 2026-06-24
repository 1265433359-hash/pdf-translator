from PySide6.QtWidgets import (QDialog, QFormLayout, QVBoxLayout, QHBoxLayout,
                               QComboBox, QLineEdit, QPlainTextEdit, QSpinBox,
                               QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                               QDialogButtonBox, QWidget, QGroupBox)
from PySide6.QtWidgets import QApplication
from pdf_translator import themes
from pdf_translator.engines.registry import engine_labels, models_for, build_engine
from pdf_translator.glossary import Glossary
from pdf_translator.workers import TranslateWorker

YOUDAO_SECRET_KEY = "youdao_secret"


class SettingsDialog(QDialog):
    """Edit engine/keys/model/prompt/concurrency/theme/glossary; show & clear cache."""

    def __init__(self, settings, cache, glossary=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.settings = settings
        self.cache = cache
        self.glossary = glossary or Glossary()

        root = QVBoxLayout(self)
        form = QFormLayout()
        root.addLayout(form)

        # 1. engine / model / custom base_url
        self.engine_box = QComboBox()
        self._engines = engine_labels()
        for name, label in self._engines:
            self.engine_box.addItem(label, name)
        idx = next((i for i, (n, _) in enumerate(self._engines)
                    if n == settings.engine), 0)
        self.engine_box.setCurrentIndex(idx)
        self.engine_box.currentIndexChanged.connect(self._on_engine_changed)
        form.addRow("引擎", self.engine_box)

        self.model_box = QComboBox()
        self.model_box.setEditable(True)  # pick a known version or type your own
        form.addRow("模型版本", self.model_box)

        self.base_url_edit = QLineEdit(settings.custom_base_url)
        self.base_url_edit.setPlaceholderText("仅自定义引擎需要")
        form.addRow("自定义 base_url", self.base_url_edit)

        # 2/3. API key (+ youdao secret)
        self.key_edit = QLineEdit(settings.get_api_key(self.current_engine()))
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("API Key / appKey", self.key_edit)

        self.secret_edit = QLineEdit(settings.get_api_key(YOUDAO_SECRET_KEY))
        self.secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("App Secret (有道)", self.secret_edit)

        # connection test
        test_wrap = QWidget(); test_row = QHBoxLayout(test_wrap)
        test_row.setContentsMargins(0, 0, 0, 0)
        self.test_btn = QPushButton("测试连接")
        self.test_btn.clicked.connect(self._test_connection)
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        test_row.addWidget(self.test_btn)
        test_row.addWidget(self.test_result, 1)
        form.addRow("验证", test_wrap)

        # 4. prompt
        self.prompt_edit = QPlainTextEdit(settings.prompt)
        self.prompt_edit.setPlaceholderText("留空使用引擎默认提示词")
        self.prompt_edit.setMaximumHeight(90)
        form.addRow("提示词", self.prompt_edit)

        # 5. concurrency
        self.concurrency_box = QSpinBox()
        self.concurrency_box.setRange(1, 16)
        self.concurrency_box.setValue(settings.concurrency)
        form.addRow("并发数", self.concurrency_box)

        # 6. theme
        self.theme_box = QComboBox()
        self._themes = themes.available_themes()
        for name in self._themes:
            self.theme_box.addItem(name, name)
        if settings.theme in self._themes:
            self.theme_box.setCurrentIndex(self._themes.index(settings.theme))
        form.addRow("主题", self.theme_box)

        # 7. glossary
        root.addWidget(self._build_glossary_group())

        # 8. cache
        root.addWidget(self._build_cache_group())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._on_engine_changed()  # set secret-field enabled state + model list
        if settings.model:
            self.model_box.setEditText(settings.model)  # restore saved model on open

    # --- helpers -----------------------------------------------------------
    def current_engine(self) -> str:
        return self.engine_box.currentData()

    def _on_engine_changed(self, *_):
        name = self.current_engine()
        self.secret_edit.setEnabled(name == "youdao")
        models = models_for(name)
        self.model_box.blockSignals(True)
        self.model_box.clear()
        self.model_box.addItems(models)
        self.model_box.setEditText(models[0] if models else "")
        self.model_box.blockSignals(False)

    def _build_glossary_group(self):
        box = QGroupBox("术语表")
        lay = QVBoxLayout(box)
        self.glossary_table = QTableWidget(0, 2)
        self.glossary_table.setHorizontalHeaderLabels(["原文", "译文"])
        self.glossary_table.horizontalHeader().setStretchLastSection(True)
        self._reload_glossary()
        lay.addWidget(self.glossary_table)

        row = QHBoxLayout()
        self.g_en = QLineEdit(); self.g_en.setPlaceholderText("English")
        self.g_zh = QLineEdit(); self.g_zh.setPlaceholderText("中文")
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._add_term)
        del_btn = QPushButton("删除选中")
        del_btn.clicked.connect(self._remove_term)
        row.addWidget(self.g_en); row.addWidget(self.g_zh)
        row.addWidget(add_btn); row.addWidget(del_btn)
        lay.addLayout(row)
        return box

    def _reload_glossary(self):
        items = sorted(self.glossary.all().items())
        self.glossary_table.setRowCount(len(items))
        for r, (en, zh) in enumerate(items):
            self.glossary_table.setItem(r, 0, QTableWidgetItem(en))
            self.glossary_table.setItem(r, 1, QTableWidgetItem(zh))

    def _add_term(self):
        en = self.g_en.text().strip()
        zh = self.g_zh.text().strip()
        if not en or not zh:
            return
        self.glossary.set(en, zh)
        self.g_en.clear(); self.g_zh.clear()
        self._reload_glossary()

    def _remove_term(self):
        row = self.glossary_table.currentRow()
        if row < 0:
            return
        item = self.glossary_table.item(row, 0)
        if item is None:
            return
        self.glossary.remove(item.text())
        self._reload_glossary()

    def _build_cache_group(self):
        box = QGroupBox("缓存")
        lay = QHBoxLayout(box)
        self.cache_label = QLabel()
        self._refresh_cache_label()
        clear_btn = QPushButton("清理缓存")
        clear_btn.clicked.connect(self._clear_cache)
        lay.addWidget(self.cache_label, 1)
        lay.addWidget(clear_btn)
        return box

    def _refresh_cache_label(self):
        mb = self.cache.size_bytes() / 1e6
        self.cache_label.setText(f"当前缓存大小：{mb:.1f} MB")

    def _clear_cache(self):
        self.cache.clear()
        self._refresh_cache_label()

    # --- connection test ---------------------------------------------------
    def _test_connection(self):
        """Build the engine from current fields and try one tiny translation."""
        name = self.current_engine()
        key = self.key_edit.text().strip()
        if not key:
            self.test_result.setText("✗ 请先填写 API Key")
            return
        try:
            eng = build_engine(
                name, key,
                model=self.model_box.currentText().strip() or None,
                prompt=None,
                base_url=self.base_url_edit.text().strip() or None,
                app_secret=self.secret_edit.text().strip() or None,
            )
        except Exception as ex:  # missing base_url/secret etc.
            self.test_result.setText(f"✗ 配置错误：{ex}")
            return
        self.test_btn.setEnabled(False)
        self.test_result.setText("测试中…")
        self._test_worker = TranslateWorker(eng, "Hello, world.", cache=None, model="")
        self._test_worker.finished_text.connect(self._on_test_ok)
        self._test_worker.failed.connect(self._on_test_fail)
        self._test_worker.start()

    def _on_test_ok(self, text):
        self.test_btn.setEnabled(True)
        self.test_result.setText(f"✓ 连接成功：{text[:40]}")

    def _on_test_fail(self, err):
        self.test_btn.setEnabled(True)
        self.test_result.setText(f"✗ 失败：{err[:80]}")

    # --- save --------------------------------------------------------------
    def save(self):
        """Persist all dialog fields into settings/keyring. Apply theme."""
        s = self.settings
        s.engine = self.current_engine()
        s.model = self.model_box.currentText().strip()
        s.custom_base_url = self.base_url_edit.text().strip()
        s.prompt = self.prompt_edit.toPlainText()
        s.concurrency = self.concurrency_box.value()
        s.theme = self.theme_box.currentData()

        key = self.key_edit.text().strip()
        if key:
            s.set_api_key(s.engine, key)
        secret = self.secret_edit.text().strip()
        if secret:
            s.set_api_key(YOUDAO_SECRET_KEY, secret)

        s.save()
        self._apply_theme()

    def _apply_theme(self):
        app = QApplication.instance()
        if app is not None:
            themes.apply_theme(app, self.settings.theme)

    def _on_accept(self):
        self.save()
        self.accept()
