import re

_WORD = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")


def is_single_word(s: str) -> bool:
    s = s.strip()
    return bool(s) and len(s) <= 30 and _WORD.match(s) is not None
