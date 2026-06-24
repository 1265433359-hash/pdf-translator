from pdf_translator import paths


def test_dirs_exist_and_files_under_them(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert paths.config_dir().exists()
    assert paths.config_file().parent == paths.config_dir()
    assert paths.cache_db().parent == paths.data_local_dir()
    assert paths.vocab_db().name == "vocab.db"
    assert paths.ecdict_db().name == "ecdict_lite.db"
