from pdf_translator.translate_queue import translate_batch, estimate_tokens
from pdf_translator.engines.base import Translator


class Flaky(Translator):
    def __init__(self): self.n = 0
    def translate(self, t, target="zh"):
        self.n += 1
        if t == "boom" and self.n < 2: raise RuntimeError("rate limit")
        return "Z" + t


def test_batch_with_cache_and_retry():
    class C:
        d = {}
        def get(self, t, m): return self.d.get((t, m))
        def put(self, t, m, v): self.d[(t, m)] = v
    prog = []
    out = translate_batch(Flaky(), ["a", "boom"], C(), "m", concurrency=1,
                          on_progress=lambda d, t: prog.append((d, t)), sleep=lambda s: None)
    assert out == ["Za", "Zboom"]
    assert prog[-1] == (2, 2)


def test_estimate_tokens():
    assert estimate_tokens(["abcd" * 10]) > 0
