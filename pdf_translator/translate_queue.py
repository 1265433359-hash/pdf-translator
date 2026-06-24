import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def estimate_tokens(paras) -> int:
    return max(1, sum(len(p) for p in paras) // 4)


def _one(engine, text, cache, model, max_retries, sleep):
    if cache:
        hit = cache.get(text, model)
        if hit is not None:
            return hit
    last = None
    for attempt in range(max_retries):
        try:
            out = engine.translate(text).strip()
            if cache:
                cache.put(text, model, out)
            return out
        except Exception as e:
            last = e
            sleep(2 ** attempt)
    raise last


def translate_batch(engine, paras, cache, model, concurrency=4, max_retries=3,
                    on_progress=None, sleep=time.sleep):
    results = [None] * len(paras)
    done = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = {ex.submit(_one, engine, p, cache, model, max_retries, sleep): i
                for i, p in enumerate(paras)}
        for fut in as_completed(futs):
            i = futs[fut]
            results[i] = fut.result()
            done += 1
            if on_progress:
                on_progress(done, len(paras))
    return results
