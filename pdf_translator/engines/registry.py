from .openai_compat import OpenAICompatEngine, DEFAULT_PROMPT

PRESETS = {
    "deepseek": {"label": "DeepSeek", "base_url": "https://api.deepseek.com/v1", "default_model": "deepseek-chat"},
    "zhipu":    {"label": "智谱 GLM", "base_url": "https://open.bigmodel.cn/api/paas/v4", "default_model": "glm-4-flash"},
    "minimax":  {"label": "MiniMax", "base_url": "https://api.minimax.chat/v1", "default_model": "MiniMax-Text-01"},
    "qwen":     {"label": "通义千问", "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "default_model": "qwen-plus"},
    "kimi":     {"label": "Kimi", "base_url": "https://api.moonshot.cn/v1", "default_model": "moonshot-v1-8k"},
    "doubao":   {"label": "豆包", "base_url": "https://ark.cn-beijing.volces.com/api/v3", "default_model": "doubao-pro"},
}


def build_engine(name, api_key, model=None, prompt=None, base_url=None):
    prompt = prompt or DEFAULT_PROMPT
    if name == "custom":
        if not base_url or not model:
            raise ValueError("custom 引擎需 base_url 与 model")
        return OpenAICompatEngine(base_url, api_key, model, prompt)
    cfg = PRESETS[name]
    return OpenAICompatEngine(cfg["base_url"], api_key, model or cfg["default_model"], prompt)


def engine_labels():
    return [(k, v["label"]) for k, v in PRESETS.items()] + [("custom", "自定义(OpenAI兼容)")]
