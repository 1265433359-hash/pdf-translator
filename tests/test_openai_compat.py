import json, httpx
from pdf_translator.engines.openai_compat import OpenAICompatEngine


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_translate_non_stream():
    def handler(req):
        return httpx.Response(200, json={"choices":[{"message":{"content":"你好世界"}}]})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert eng.translate("Hello world") == "你好世界"


def test_translate_sends_model_and_key():
    seen = {}
    def handler(req):
        seen["auth"] = req.headers.get("authorization")
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices":[{"message":{"content":"x"}}]})
    eng = OpenAICompatEngine("https://x/v1", "secret", "deepseek-chat", http=make_client(handler))
    eng.translate("hi")
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["model"] == "deepseek-chat"
