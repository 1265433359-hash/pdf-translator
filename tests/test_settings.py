import keyring
from keyring.backends.fail import Keyring as FailKeyring
from pdf_translator import settings as S

class MemKeyring(FailKeyring):
    store = {}
    def set_password(self, s, u, p): MemKeyring.store[(s,u)] = p
    def get_password(self, s, u): return MemKeyring.store.get((s,u))

def test_load_ignores_unknown_json_keys(tmp_path, monkeypatch):
    import json
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cfg = S.paths.config_file()
    cfg.write_text(json.dumps({"engine": "qwen", "totally_unknown_key": 123}),
                   encoding="utf-8")
    s = S.Settings.load()  # must not raise on the unknown key
    assert s.engine == "qwen"
    assert not hasattr(s, "totally_unknown_key")


def test_roundtrip_config(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    keyring.set_keyring(MemKeyring())
    s = S.Settings.load()
    s.engine = "deepseek"; s.set_api_key("deepseek", "secret"); s.save()
    s2 = S.Settings.load()
    assert s2.engine == "deepseek"
    assert s2.get_api_key("deepseek") == "secret"
