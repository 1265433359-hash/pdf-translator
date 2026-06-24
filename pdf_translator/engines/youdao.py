import hashlib
import time
import uuid

import httpx

from .base import Translator

API = "https://openapi.youdao.com/api"


def _truncate(q: str) -> str:
    n = len(q)
    return q if n <= 20 else q[:10] + str(n) + q[-10:]


def _sign(app_key, q, salt, curtime, app_secret):
    s = app_key + _truncate(q) + salt + curtime + app_secret
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class YoudaoEngine(Translator):
    def __init__(self, app_key, app_secret, http=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self._http = http or httpx.Client(timeout=30)

    def translate(self, text, target="zh"):
        salt = str(uuid.uuid4())
        curtime = str(int(time.time()))
        data = {
            "q": text,
            "from": "en",
            "to": "zh-CHS",
            "appKey": self.app_key,
            "salt": salt,
            "sign": _sign(self.app_key, text, salt, curtime, self.app_secret),
            "signType": "v3",
            "curtime": curtime,
        }
        r = self._http.post(API, data=data)
        r.raise_for_status()
        return r.json()["translation"][0]
