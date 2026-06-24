from pdf_translator.engines.registry import PRESETS, build_engine, engine_labels


def test_presets_have_required_keys():
    for name in ["deepseek", "zhipu", "minimax", "qwen", "kimi", "doubao"]:
        assert name in PRESETS
        assert PRESETS[name]["base_url"].startswith("http")
        assert PRESETS[name]["default_model"]


def test_build_preset_uses_default_model():
    eng = build_engine("deepseek", "k")
    assert eng.model == PRESETS["deepseek"]["default_model"]


def test_build_custom_requires_base_url():
    eng = build_engine("custom", "k", model="my-model", base_url="https://my/v1")
    assert eng.base_url == "https://my/v1" and eng.model == "my-model"


def test_engine_labels_includes_youdao():
    assert ("youdao", "有道翻译") in engine_labels()


def test_build_preset_threads_glossary():
    from pdf_translator.glossary import Glossary
    g = Glossary.__new__(Glossary)  # bypass file load
    g._d = {}
    eng = build_engine("deepseek", "k", glossary=g)
    assert eng.glossary is g


def test_build_youdao_threads_app_secret():
    from pdf_translator.engines.youdao import YoudaoEngine
    eng = build_engine("youdao", "my-app-key", app_secret="my-app-secret")
    assert isinstance(eng, YoudaoEngine)
    assert eng.app_key == "my-app-key" and eng.app_secret == "my-app-secret"


def test_models_for_known_and_unknown():
    from pdf_translator.engines.registry import models_for
    assert "deepseek-chat" in models_for("deepseek")
    assert "qwen-plus" in models_for("qwen")
    assert models_for("custom") == []
    assert models_for("nonexistent") == []
