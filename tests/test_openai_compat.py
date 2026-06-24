import json, httpx
from pdf_translator.engines.openai_compat import OpenAICompatEngine
from pdf_translator.glossary import Glossary


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


def test_translate_injects_matching_glossary_term_into_system(tmp_path):
    seen = {}
    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices":[{"message":{"content":"x"}}]})
    g = Glossary(tmp_path / "g.json")
    g.set("transformer", "变换器")
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler), glossary=g)
    eng.translate("The transformer architecture")
    system = seen["body"]["messages"][0]["content"]
    assert "transformer" in system and "变换器" in system


def _sse(*deltas):
    lines = []
    for d in deltas:
        lines.append('data: ' + json.dumps({"choices":[{"delta":{"content":d}}]}))
    lines.append("data: [DONE]")
    return "\n\n".join(lines) + "\n\n"


def test_translate_stream_yields_deltas_in_order():
    def handler(req):
        return httpx.Response(200, content=_sse("你好", "世界", "！"),
                              headers={"content-type": "text/event-stream"})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert list(eng.translate_stream("Hello world!")) == ["你好", "世界", "！"]


def test_translate_stream_skips_malformed_lines():
    body = ("data: " + json.dumps({"choices":[{"delta":{"content":"你好"}}]}) + "\n\n"
            "data: not-json\n\n"
            "data: " + json.dumps({"choices":[{"delta":{"content":"世界"}}]}) + "\n\n"
            "data: [DONE]\n\n")
    def handler(req):
        return httpx.Response(200, content=body,
                              headers={"content-type": "text/event-stream"})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert list(eng.translate_stream("hi")) == ["你好", "世界"]


def test_lookup_word_parses_json_wrapped_in_prose():
    content = ('Here is the JSON: {"phonetic":"/həˈləʊ/",'
               '"meanings":["int. 你好"],"collocations":["say hello"],'
               '"examples":["Hello there."]} Hope it helps.')
    def handler(req):
        return httpx.Response(200, json={"choices":[{"message":{"content":content}}]})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    entry = eng.lookup_word("hello")
    assert entry is not None
    assert entry.word == "hello"
    assert entry.phonetic == "/həˈləʊ/"
    assert entry.meanings == ["int. 你好"]
    assert entry.collocations == ["say hello"]
    assert entry.examples == ["Hello there."]


def test_lookup_word_returns_none_on_error_status():
    def handler(req):
        return httpx.Response(500, text="boom")
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert eng.lookup_word("hello") is None


def test_lookup_word_returns_none_on_non_json_content():
    def handler(req):
        return httpx.Response(200, json={"choices":[{"message":{"content":"sorry no idea"}}]})
    eng = OpenAICompatEngine("https://x/v1", "k", "m", http=make_client(handler))
    assert eng.lookup_word("hello") is None


def test_list_models_parses_data_ids():
    import httpx
    from pdf_translator.engines.openai_compat import OpenAICompatEngine
    def handler(req):
        assert req.url.path.endswith("/models")
        return httpx.Response(200, json={"data": [{"id": "m-b"}, {"id": "m-a"}, {"x": 1}]})
    eng = OpenAICompatEngine("https://x/v1", "k", "m",
                             http=httpx.Client(transport=httpx.MockTransport(handler)))
    assert eng.list_models() == ["m-a", "m-b"]  # sorted, skips entries without id
