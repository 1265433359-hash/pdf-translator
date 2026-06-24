import json
import httpx

from pdf_translator.engines.registry import build_engine, PRESETS
from pdf_translator.engines import registry as reg
from pdf_translator.glossary import Glossary


def test_build_engine_threads_prompt_and_glossary_into_system(tmp_path, monkeypatch):
    """Regression for the seam unit tests missed: a custom prompt AND a glossary
    term must both reach the system message when going through build_engine()."""
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "x"}}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    # Force OpenAICompatEngine to use our mock transport regardless of preset.
    real_init = reg.OpenAICompatEngine.__init__

    def patched_init(self, base_url, api_key, model, prompt=reg.DEFAULT_PROMPT,
                     http=None, glossary=None):
        real_init(self, base_url, api_key, model, prompt, http=client, glossary=glossary)

    monkeypatch.setattr(reg.OpenAICompatEngine, "__init__", patched_init)

    g = Glossary(tmp_path / "g.json")
    g.set("transformer", "变换器")

    eng = build_engine("deepseek", "k", prompt="CUSTOM-PROMPT-XYZ", glossary=g)
    eng.translate("The transformer architecture is powerful")

    system = seen["body"]["messages"][0]["content"]
    assert "CUSTOM-PROMPT-XYZ" in system     # custom prompt reaches output
    assert "transformer" in system and "变换器" in system  # glossary reaches output
