from pdf_translator.workers import stream_translate
from pdf_translator.engines.base import Translator


class Dummy(Translator):
    def translate(self, t, target="zh"): return "你好"


def test_stream_translate_uses_cache():
    calls = {"n": 0}

    class C:
        def get(self, t, m): return "缓存值" if calls["n"] else None
        def put(self, t, m, v): calls["n"] += 1

    chunks = []
    out = stream_translate(Dummy(), "hi", C(), "m", on_chunk=chunks.append)
    assert out == "你好"   # 首次未命中
    out2 = stream_translate(Dummy(), "hi", C(), "m", on_chunk=chunks.append)
    assert out2 == "缓存值"
