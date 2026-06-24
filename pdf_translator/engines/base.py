from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class WordEntry:
    word: str
    phonetic: str = ""
    meanings: list[str] = field(default_factory=list)
    collocations: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)


class Translator(ABC):
    @abstractmethod
    def translate(self, text: str, target: str = "zh") -> str: ...

    def translate_stream(self, text: str, target: str = "zh") -> Iterator[str]:
        yield self.translate(text, target)

    def lookup_word(self, word: str) -> "WordEntry | None":
        return None
