import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import keyring
from keyring.backends.fail import Keyring as FailKeyring
from PySide6.QtWidgets import QApplication

from pdf_translator import settings as S
from pdf_translator.cache import TranslationCache
from pdf_translator.settings_dialog import SettingsDialog, YOUDAO_SECRET_KEY
from pdf_translator.glossary import Glossary


class MemKeyring(FailKeyring):
    store = {}
    def set_password(self, s, u, p): MemKeyring.store[(s, u)] = p
    def get_password(self, s, u): return MemKeyring.store.get((s, u))


def _app():
    return QApplication.instance() or QApplication([])


def _setup(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    MemKeyring.store = {}
    keyring.set_keyring(MemKeyring())


def test_save_persists_settings_and_keys(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _app()
    settings = S.Settings.load()
    cache = TranslationCache(db_path=str(tmp_path / "cache.db"))
    glossary = Glossary(path=str(tmp_path / "glossary.json"))

    dlg = SettingsDialog(settings, cache, glossary=glossary)
    # Set fields programmatically (engine youdao to exercise secret field).
    dlg.engine_box.setCurrentIndex(
        next(i for i in range(dlg.engine_box.count())
             if dlg.engine_box.itemData(i) == "youdao"))
    dlg.model_box.setEditText("my-model")
    dlg.base_url_edit.setText("https://example/v1")
    dlg.prompt_edit.setPlainText("custom prompt")
    dlg.concurrency_box.setValue(8)
    dlg.key_edit.setText("app-key")
    dlg.secret_edit.setText("app-secret")
    assert dlg.secret_edit.isEnabled()  # youdao -> secret field on

    dlg.save()

    s2 = S.Settings.load()
    assert s2.engine == "youdao"
    assert s2.model == "my-model"
    assert s2.custom_base_url == "https://example/v1"
    assert s2.prompt == "custom prompt"
    assert s2.concurrency == 8
    assert s2.get_api_key("youdao") == "app-key"
    assert s2.get_api_key(YOUDAO_SECRET_KEY) == "app-secret"


def test_glossary_add_remove(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _app()
    settings = S.Settings.load()
    cache = TranslationCache(db_path=str(tmp_path / "cache.db"))
    glossary = Glossary(path=str(tmp_path / "glossary.json"))

    dlg = SettingsDialog(settings, cache, glossary=glossary)
    dlg.g_en.setText("token"); dlg.g_zh.setText("词元")
    dlg._add_term()
    assert glossary.all() == {"token": "词元"}
    assert dlg.glossary_table.rowCount() == 1

    dlg.glossary_table.setCurrentCell(0, 0)
    dlg._remove_term()
    assert glossary.all() == {}
    assert dlg.glossary_table.rowCount() == 0


def test_clear_cache_updates_label(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _app()
    settings = S.Settings.load()
    cache = TranslationCache(db_path=str(tmp_path / "cache.db"))
    cache.put("hello world", "m", "你好世界")
    glossary = Glossary(path=str(tmp_path / "glossary.json"))

    dlg = SettingsDialog(settings, cache, glossary=glossary)
    assert "MB" in dlg.cache_label.text()
    dlg._clear_cache()
    assert cache.get("hello world", "m") is None
    assert "0.0 MB" in dlg.cache_label.text()


def test_app_window_has_settings_action(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    _app()
    from pdf_translator.app_window import MainWindow
    w = MainWindow()
    assert hasattr(w, "settings_action")
    assert w.settings_action.text() == "设置"
