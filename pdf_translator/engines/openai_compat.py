import json
import httpx
from typing import Iterator
from .base import Translator, WordEntry

DEFAULT_PROMPT = "你是专业学术翻译。把用户给的英文准确译成中文，术语规范，只输出译文，不要解释。"


class OpenAICompatEngine(Translator):
    def __init__(self, base_url, api_key, model, prompt=DEFAULT_PROMPT, http=None, glossary=None):
        self.base_url = base_url.rstrip("/"); self.api_key = api_key
        self.model = model; self.prompt = prompt
        self.glossary = glossary
        self._http = http or httpx.Client(timeout=60)

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _system(self, text):
        return self.glossary.apply_to_prompt(self.prompt, text) if self.glossary else self.prompt

    def translate(self, text, target="zh"):
        body = {"model": self.model, "messages": [
            {"role": "system", "content": self._system(text)},
            {"role": "user", "content": text}]}
        r = self._http.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=body)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def translate_stream(self, text, target="zh") -> Iterator[str]:
        body = {"model": self.model, "stream": True, "messages": [
            {"role": "system", "content": self._system(text)},
            {"role": "user", "content": text}]}
        with self._http.stream("POST", f"{self.base_url}/chat/completions",
                               headers=self._headers(), json=body) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith("data:"): continue
                data = line[5:].strip()
                if data == "[DONE]": break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                    if delta: yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    def lookup_word(self, word) -> WordEntry | None:
        instr = ('返回该英文单词的 JSON：{"phonetic":"音标","meanings":["词性. 释义"],'
                 '"collocations":["固定搭配"],"examples":["例句"]}，只输出 JSON。单词：' + word)
        body = {"model": self.model, "messages": [{"role": "user", "content": instr}]}
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=body)
            r.raise_for_status()
            raw = r.json()["choices"][0]["message"]["content"]
            raw = raw[raw.find("{"): raw.rfind("}") + 1]
            d = json.loads(raw)
            return WordEntry(word=word, phonetic=d.get("phonetic",""),
                             meanings=d.get("meanings",[]), collocations=d.get("collocations",[]),
                             examples=d.get("examples",[]))
        except Exception:
            return None
