import math
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field


def idf_a1(n_docs: int, df: int) -> float:
    """A1, Eq. 1."""
    if df <= 0 or n_docs < df:
        raise ValueError(f"df inválido: N={n_docs}, df={df}")
    return math.log10(n_docs / df)


def idf_smooth(n_docs: int, df: int) -> float:
    """Guia 0.3 (não vem de artigo)."""
    if df < 0 or n_docs < df:
        raise ValueError(f"df inválido: N={n_docs}, df={df}")
    return math.log((1 + n_docs) / (1 + df)) + 1


def term_frequencies(tokens: Iterable[str]) -> Counter:
    return Counter(tokens)


def tfidf(tf: Mapping[str, int], idf: Callable[[str], float]) -> dict[str, float]:
    return {term: count * idf(term) for term, count in tf.items()}


def cosine(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    dot = sum(weight * b[term] for term, weight in a.items() if term in b)
    norm_a = math.sqrt(sum(w * w for w in a.values()))
    norm_b = math.sqrt(sum(w * w for w in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def document_frequencies(documents: Iterable[Iterable[str]]) -> tuple[int, Counter]:
    df: Counter = Counter()
    n_docs = 0
    for tokens in documents:
        n_docs += 1
        df.update(set(tokens))
    return n_docs, df


def a1_tfidf_vectors(documents: Mapping[str, Iterable[str]]) -> dict[str, dict[str, float]]:
    """TF-IDF do A1 dentro de uma coleção fechada (N = nº de documentos da coleção)."""
    tfs = {name: term_frequencies(tokens) for name, tokens in documents.items()}
    n_docs, df = document_frequencies(tf.keys() for tf in tfs.values())
    return {name: tfidf(tf, lambda t: idf_a1(n_docs, df[t])) for name, tf in tfs.items()}


@dataclass(frozen=True)
class ReferenceIdf:
    n_docs: int
    df: Mapping[str, int] = field(repr=False)
    version: str = ""

    def __call__(self, term: str) -> float:
        return idf_smooth(self.n_docs, self.df.get(term, 0))

    def vector(self, tokens: Iterable[str]) -> dict[str, float]:
        return tfidf(term_frequencies(tokens), self)
