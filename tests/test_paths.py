import sys

from pdf_translator import paths


def test_bundled_data_dir_uses_meipass_when_frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert paths.bundled_data_dir() == tmp_path / "data"


def test_bundled_data_dir_falls_back_to_repo(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    from pathlib import Path
    expected = Path(paths.__file__).resolve().parent.parent / "data"
    assert paths.bundled_data_dir() == expected


def test_dirs_exist_and_files_under_them(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert paths.config_dir().exists()
    assert paths.config_file().parent == paths.config_dir()
    assert paths.cache_db().parent == paths.data_local_dir()
    assert paths.vocab_db().name == "vocab.db"
    assert paths.ecdict_db().name == "ecdict_lite.db"
