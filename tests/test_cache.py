from pdf_translator.cache import TranslationCache


def test_put_get_and_clear(tmp_path):
    c = TranslationCache(tmp_path / "c.db")
    assert c.get("hello", "m1") is None
    c.put("hello", "m1", "你好")
    assert c.get("hello", "m1") == "你好"
    assert c.get("hello", "m2") is None      # 换模型不命中
    assert c.size_bytes() > 0
    c.clear()
    assert c.get("hello", "m1") is None
