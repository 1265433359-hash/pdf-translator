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
