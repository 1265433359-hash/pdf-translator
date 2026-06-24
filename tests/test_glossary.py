from pdf_translator.glossary import Glossary


def test_apply_injects_only_present_terms(tmp_path):
    g = Glossary(tmp_path / "g.json")
    g.set("transformer", "变换器"); g.set("kernel", "核")
    prompt = g.apply_to_prompt("BASE", "The transformer architecture")
    assert "transformer" in prompt and "变换器" in prompt
    assert "kernel" not in prompt    # 未出现的不注入
