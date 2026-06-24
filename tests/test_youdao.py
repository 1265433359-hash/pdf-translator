import httpx
from pdf_translator.engines.youdao import YoudaoEngine, _truncate, _sign


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_truncate_rule():
    assert _truncate("abcdefg") == "abcdefg"             # <=20 原样
    long = "a" * 30
    assert _truncate(long) == long[:10] + str(30) + long[-10:]  # 前10+len+后10


def test_sign_matches_sha256_formula():
    import hashlib
    sig = _sign("ak", "hello", "salt", "123", "sk")
    expected = hashlib.sha256(("ak" + "hello" + "salt" + "123" + "sk").encode("utf-8")).hexdigest()
    assert sig == expected


def test_translate_parses():
    def handler(req):
        return httpx.Response(200, json={"translation": ["你好"]})
    eng = YoudaoEngine("ak", "sk", http=make_client(handler))
    assert eng.translate("hello") == "你好"


def test_translate_sends_signature_fields():
    seen = {}

    def handler(req):
        from urllib.parse import parse_qs
        seen["form"] = {k: v[0] for k, v in parse_qs(req.content.decode()).items()}
        return httpx.Response(200, json={"translation": ["你好"]})
    eng = YoudaoEngine("ak", "sk", http=make_client(handler))
    eng.translate("hello")
    form = seen["form"]
    assert form["appKey"] == "ak"
    assert form["signType"] == "v3"
    assert form["from"] == "en" and form["to"] == "zh-CHS"
    assert form["q"] == "hello"
    assert "salt" in form and "curtime" in form
    assert form["sign"] == _sign("ak", "hello", form["salt"], form["curtime"], "sk")
