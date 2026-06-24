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


def test_retry_delay_429_backs_off_longer_and_honors_retry_after():
    from pdf_translator.translate_queue import _retry_delay

    class Resp:
        def __init__(self, status, headers=None):
            self.status_code = status
            self.headers = headers or {}

    class Err(Exception):
        def __init__(self, resp):
            self.response = resp

    # plain error -> exponential base
    assert _retry_delay(RuntimeError("x"), 0) == 1
    assert _retry_delay(RuntimeError("x"), 2) == 4
    # 429 without header -> longer than base
    assert _retry_delay(Err(Resp(429)), 0) >= 5
    # 429 with Retry-After honored
    assert _retry_delay(Err(Resp(429, {"Retry-After": "30"})), 0) == 30
