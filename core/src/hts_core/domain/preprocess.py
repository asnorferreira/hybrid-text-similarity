import re
from collections.abc import Callable, Iterable, Sequence

# (forma, lema) por token; quem lematiza é o adapter (spaCy), o domínio só filtra
Analyzer = Callable[[str], Sequence[tuple[str, str]]]

_URL = re.compile(r"https?://\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_NON_LETTER = re.compile(r"[^\w\s]|[\d_]")
_SPACES = re.compile(r"\s+")
_CONTROL = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]")

MIN_TOKEN_LENGTH = 3


def remove_noise(text: str) -> str:
    text = _URL.sub(" ", text)
    text = _EMAIL.sub(" ", text)
    text = _NON_LETTER.sub(" ", text)
    return _SPACES.sub(" ", text).strip()


def lexical_tokens(text: str, analyze: Analyzer, stopwords: Iterable[str]) -> list[str]:
    stop = stopwords if isinstance(stopwords, (set, frozenset)) else frozenset(stopwords)
    tokens = []
    for form, lemma in analyze(remove_noise(text.lower())):
        if form.lower() in stop:
            continue
        for part in lemma.lower().split():
            if part.isalpha() and len(part) >= MIN_TOKEN_LENGTH and part not in stop:
                tokens.append(part)
    return tokens


def semantic_text(text: str) -> str:
    return _SPACES.sub(" ", _CONTROL.sub(" ", text)).strip()
