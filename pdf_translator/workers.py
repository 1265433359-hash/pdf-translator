from PySide6.QtCore import QThread, Signal

from pdf_translator.translate_queue import translate_batch


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


class BatchTranslateWorker(QThread):
    """Translate a list of paragraphs off the GUI thread.

    Progress is marshaled back to the GUI thread via the ``progress`` signal;
    the final list of translations via ``done``. Never touch widgets from run()."""
    progress = Signal(int, int)        # (done, total)
    done = Signal(list)                # list[str] of translations
    failed = Signal(str)

    def __init__(self, engine, paras, cache=None, model="", concurrency=4):
        super().__init__()
        self._engine = engine
        self._paras = paras
        self._cache = cache
        self._model = model
        self._concurrency = concurrency

    def run(self):
        try:
            results = translate_batch(
                self._engine, self._paras, self._cache, self._model,
                concurrency=self._concurrency,
                on_progress=lambda d, t: self.progress.emit(d, t),
            )
            self.done.emit(results)
        except Exception as e:
            self.failed.emit(str(e))


class WordLookupWorker(QThread):
    """Run engine.lookup_word(word) off the main thread to enrich a WordEntry
    with collocations/examples (network call). Emits the resulting WordEntry."""
    found = Signal(object); failed = Signal(str)

    def __init__(self, engine, word):
        super().__init__(); self._engine = engine; self._word = word

    def run(self):
        try:
            entry = self._engine.lookup_word(self._word)
            if entry is not None:
                self.found.emit(entry)
        except Exception as e:
            self.failed.emit(str(e))
