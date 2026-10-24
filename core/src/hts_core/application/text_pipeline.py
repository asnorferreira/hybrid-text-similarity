from dataclasses import dataclass

from hts_core.domain.preprocess import Analyzer, lexical_tokens, semantic_text
from hts_core.domain.text import split_sentences, word_count


@dataclass(frozen=True)
class Sentence:
    index: int
    raw: str
    semantic: str
    lexical: tuple[str, ...]
    words: int


def prepare_sentences(clean_text: str, analyze: Analyzer, stopwords: frozenset[str]) -> list[Sentence]:
    return [
        Sentence(
            index=i,
            raw=raw,
            semantic=semantic_text(raw),
            lexical=tuple(lexical_tokens(raw, analyze, stopwords)),
            words=word_count(raw),
        )
        for i, raw in enumerate(split_sentences(clean_text))
    ]
