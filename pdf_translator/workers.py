from PySide6.QtCore import QThread, Signal


def stream_translate(engine, text, cache, model, on_chunk):
    if cache:
        hit = cache.get(text, model)
        if hit is not None:
            on_chunk(hit); return hit
    parts = []
    for c in engine.translate_stream(text):
        parts.append(c); on_chunk(c)
    out = "".join(parts).strip()
    if cache: cache.put(text, model, out)
    return out


class TranslateWorker(QThread):
    chunk = Signal(str); finished_text = Signal(str); failed = Signal(str)

    def __init__(self, engine, text, cache=None, model=""):
        super().__init__(); self._engine = engine; self._text = text
        self._cache = cache; self._model = model

    def run(self):
        try:
            out = stream_translate(self._engine, self._text, self._cache, self._model, self.chunk.emit)
            self.finished_text.emit(out)
        except Exception as e:
            self.failed.emit(str(e))
