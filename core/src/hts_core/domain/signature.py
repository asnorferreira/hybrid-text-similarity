import hashlib
from collections.abc import Iterable, Mapping

SALIENT_TOP_K = 30
_MOD = 2**64


def stable_hash64(term: str) -> int:
    return int.from_bytes(hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest(), "big")


def signature(terms: Iterable[str]) -> int:
    return sum(stable_hash64(t) for t in set(terms)) % _MOD


def salient_terms(weights: Mapping[str, float], k: int = SALIENT_TOP_K) -> list[str]:
    ranked = sorted(weights.items(), key=lambda item: (-item[1], item[0]))
    return [term for term, weight in ranked[:k] if weight > 0]


def term_difference_by_term_count(terms_1: Iterable[str], terms_2: Iterable[str]) -> float:
    """Adaptação do projeto: doc2 menos doc1, dividido pela menor quantidade de termos."""
    t1, t2 = set(terms_1), set(terms_2)
    smaller = min(len(t1), len(t2))
    if smaller == 0:
        return 0.0 if not t1 and not t2 else 1.0
    return len(t2 - t1) / smaller


def term_difference(terms_1: Iterable[str], terms_2: Iterable[str], size_1: int, size_2: int,
                    *, direction: str) -> float:
    """A3, pp. 247/250: tamanho externo; direção explícita devido ao conflito SQL/prosa."""
    if size_1 < 0 or size_2 < 0:
        raise ValueError("tamanhos devem ser não negativos e estar na mesma unidade")
    t1, t2 = set(terms_1), set(terms_2)
    if size_1 == size_2 and len(t1) != len(t2):
        raise ValueError("A3 não define desempate de tamanho com quantidades de termos diferentes")
    denominator = len(t1) if size_1 <= size_2 else len(t2)
    if denominator == 0:
        raise ValueError("A3 não define fração com denominador vazio")
    if direction == "doc1_minus_doc2":
        numerator = len(t1 - t2)
    elif direction == "doc2_minus_doc1":
        numerator = len(t2 - t1)
    else:
        raise ValueError("direção deve ser doc1_minus_doc2 (SQL) ou doc2_minus_doc1 (prosa)")
    return numerator / denominator


def a3_relation(delta: float, size_1: int, size_2: int) -> str:
    """Rótulos do projeto sobre os limiares de A3, pp. 247–250."""
    ratio = max(size_1, size_2) / min(size_1, size_2) if min(size_1, size_2) > 0 else float("inf")
    if delta < 0.10 and ratio <= 1.10:
        return "muito_similar"
    if delta < 0.20:
        return "relacionado"
    if delta < 0.50 and ratio <= 1.50:
        return "texto_inserido"
    return "distinto"
