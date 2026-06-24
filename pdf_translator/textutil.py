import re

_WORD = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")
# leading/trailing punctuation & symbols (keep word-internal hyphen/apostrophe)
_EDGE = re.compile(r"^[^0-9A-Za-z一-鿿]+|[^0-9A-Za-z一-鿿]+$")


def strip_edge_punct(s: str) -> str:
    """Drop punctuation/symbols at the very start/end (e.g. 'world.' -> 'world',
    '(BJP)' -> 'BJP'), keeping internal hyphens/apostrophes."""
    return _EDGE.sub("", s.strip())


def is_single_word(s: str) -> bool:
    s = s.strip()
    return bool(s) and len(s) <= 30 and _WORD.match(s) is not None
