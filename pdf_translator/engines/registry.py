from .openai_compat import OpenAICompatEngine, DEFAULT_PROMPT
from .youdao import YoudaoEngine

PRESETS = {
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "default_model": "deepseek-chat"},
    "zhipu":    {"label": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "default_model": "glm-4-flash"},
    "minimax":  {"label": "MiniMax", "base_url": "https://api.minimax.chat/v1", "default_model": "MiniMax-Text-01"},
    "qwen":     {"label": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-plus"},
    "kimi":     {"label": "Kimi", "base_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k"},
    "doubao":   {"label": "豆包", "base_url": "https://ark.cn-beijing.volces.com/api/v3", "default_model": "doubao-pro"},
}

# 各引擎常见可选模型版本(供设置界面下拉;仍可手动输入其它型号)
MODELS = {
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "zhipu":    ["glm-4-flash", "glm-4-air", "glm-4-plus", "glm-4", "glm-4-long"],
    "minimax":  ["MiniMax-Text-01", "abab6.5s-chat"],
    "qwen":     ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-long"],
    "kimi":     ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
    "doubao":   ["doubao-pro-32k", "doubao-pro-4k", "doubao-lite-32k"],
    "custom":   [],
    "youdao":   [],
}


def models_for(name):
    """Common model versions for an engine (may be empty; field stays editable)."""
    return MODELS.get(name, [])


def build_engine(name, api_key, model=None, prompt=None, base_url=None,
                 app_secret=None, glossary=None):
    prompt = prompt or DEFAULT_PROMPT
    if name == "youdao":
        if not app_secret:
            raise ValueError("youdao 引擎需 appKey(api_key) 与 appSecret(app_secret)")
        return YoudaoEngine(api_key, app_secret)
    if name == "custom":
        if not base_url or not model:
            raise ValueError("custom 引擎需 base_url 与 model")
        return OpenAICompatEngine(base_url, api_key, model, prompt, glossary=glossary)
    cfg = PRESETS[name]
    return OpenAICompatEngine(cfg["base_url"], api_key, model or cfg["default_model"],
                             prompt, glossary=glossary)


def engine_labels():
    return [(k, v["label"]) for k, v in PRESETS.items()] + [
        ("youdao", "有道翻译"),
        ("custom", "自定义(OpenAI兼容)"),
    ]
