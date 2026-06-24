import threading

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


def test_thread_safe(tmp_path):
    c = TranslationCache(tmp_path / "t.db")
    errors = []

    def work():
        try:
            c.put("k", "m", "v")
            assert c.get("k", "m") == "v"
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=work) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
