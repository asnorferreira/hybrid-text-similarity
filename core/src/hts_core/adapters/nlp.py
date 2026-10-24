from functools import lru_cache

import spacy
from spacy.lang.pt.stop_words import STOP_WORDS

SPACY_MODEL = "pt_core_news_sm"
STOPWORDS = frozenset(STOP_WORDS)


@lru_cache(maxsize=1)
def _nlp():
    return spacy.load(SPACY_MODEL, disable=["parser", "ner"])


def analyze(text: str) -> list[tuple[str, str]]:
    return [(token.text, token.lemma_) for token in _nlp()(text) if not token.is_space]


def model_info() -> dict:
    meta = _nlp().meta
    return {"name": f"{meta['lang']}_{meta['name']}", "version": meta["version"], "license": meta["license"]}
