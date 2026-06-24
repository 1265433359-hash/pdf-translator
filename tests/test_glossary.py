from pdf_translator.glossary import Glossary


def test_apply_injects_only_present_terms(tmp_path):
    g = Glossary(tmp_path / "g.json")
    g.set("transformer", "变换器"); g.set("kernel", "核")
    prompt = g.apply_to_prompt("BASE", "The transformer architecture")
    assert "transformer" in prompt and "变换器" in prompt
    assert "kernel" not in prompt    # 未出现的不注入


def test_apply_uses_word_boundary_not_substring(tmp_path):
    g = Glossary(tmp_path / "g.json")
    g.set("net", "网")
    # "net" must NOT fire inside "network"...
    assert g.apply_to_prompt("BASE", "The network layer") == "BASE"
    # ...but DOES fire as a standalone word.
    prompt = g.apply_to_prompt("BASE", "A neural net is trained")
    assert "net" in prompt and "网" in prompt


def test_corrupt_glossary_file_loads_empty(tmp_path):
    p = tmp_path / "g.json"
    p.write_text("{ this is not valid json", encoding="utf-8")
    g = Glossary(p)  # must not raise
    assert g.all() == {}
