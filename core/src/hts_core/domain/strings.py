from collections.abc import Iterable

from hts_core.domain.lexical import cosine, term_frequencies

JW_PREFIX_SCALE = 0.1
JW_MAX_PREFIX = 4
SW_MATCH = 2
SW_MISMATCH = -1
SW_GAP = -1
NGRAM_N = 3


def levenshtein_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def damerau_levenshtein_distance(a: str, b: str) -> int:
    """Forma OSA: Levenshtein + transposição de adjacentes (mapa, Art. 5)."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    before_previous = previous
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            value = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                value = min(value, before_previous[j - 2] + 1)
            current.append(value)
        before_previous, previous = previous, current
    return previous[-1]


def edit_similarity(distance: int, a: str, b: str) -> float:
    """A4, Eq. 2."""
    longest = max(len(a), len(b))
    return 1.0 if longest == 0 else 1.0 - distance / longest


def levenshtein(a: str, b: str) -> float:
    return edit_similarity(levenshtein_distance(a, b), a, b)


def damerau_levenshtein(a: str, b: str) -> float:
    return edit_similarity(damerau_levenshtein_distance(a, b), a, b)


def jaro_counts(s1: str, s2: str) -> tuple[int, int]:
    """Devolve (m, casamentos fora de ordem)."""
    len1, len2 = len(s1), len(s2)
    window = max(max(len1, len2) // 2 - 1, 0)
    matched1 = [False] * len1
    matched2 = [False] * len2
    m = 0
    for i, c in enumerate(s1):
        for j in range(max(0, i - window), min(i + window + 1, len2)):
            if not matched2[j] and s2[j] == c:
                matched1[i] = matched2[j] = True
                m += 1
                break
    out_of_order = 0
    k = 0
    for i in range(len1):
        if matched1[i]:
            while not matched2[k]:
                k += 1
            if s1[i] != s2[k]:
                out_of_order += 1
            k += 1
    return m, out_of_order


def jaro(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    m, out_of_order = jaro_counts(s1, s2)
    if m == 0:
        return 0.0
    # metade exata, como no mapa; rapidfuzz e o strcmp95 arredondam para baixo (TCC/14)
    t = out_of_order / 2
    return (m / len1 + m / len2 + (m - t) / m) / 3


def common_prefix(s1: str, s2: str, limit: int = JW_MAX_PREFIX) -> int:
    length = 0
    for c1, c2 in zip(s1[:limit], s2[:limit]):
        if c1 != c2:
            break
        length += 1
    return length


def jaro_winkler(s1: str, s2: str, p: float = JW_PREFIX_SCALE) -> float:
    """A4, Eq. 4, sem o limiar de 0,7 que outras implementações usam."""
    if not 0 <= p <= 0.25:
        raise ValueError("p deve estar entre 0 e 0,25")
    sim_j = jaro(s1, s2)
    return sim_j + common_prefix(s1, s2) * p * (1 - sim_j)


def smith_waterman_score(a: str, b: str, match: int = SW_MATCH, mismatch: int = SW_MISMATCH,
                         gap: int = SW_GAP) -> int:
    if len(a) < len(b):
        a, b = b, a
    best = 0
    previous = [0] * (len(b) + 1)
    for ca in a:
        current = [0]
        for j, cb in enumerate(b, 1):
            score = max(0, previous[j - 1] + (match if ca == cb else mismatch),
                        previous[j] + gap, current[j - 1] + gap)
            current.append(score)
            best = max(best, score)
        previous = current
    return best


def smith_waterman(a: str, b: str) -> float:
    """Escore local normalizado pelo máximo possível, match × menor comprimento."""
    shortest = min(len(a), len(b))
    if shortest == 0:
        return 1.0 if len(a) == len(b) else 0.0
    return smith_waterman_score(a, b) / (SW_MATCH * shortest)


def char_ngrams(text: str, n: int = NGRAM_N) -> set[str]:
    if n < 1:
        raise ValueError("n deve ser positivo")
    if len(text) < n:
        return {text} if text else set()
    return {text[i:i + n] for i in range(len(text) - n + 1)}


def ngram_dice(a: str, b: str, n: int = NGRAM_N) -> float:
    """A4, Eq. 7 (Dice)."""
    x, y = char_ngrams(a, n), char_ngrams(b, n)
    if not x and not y:
        return 1.0
    return 2 * len(x & y) / (len(x) + len(y))


def vsm_cosine(tokens_a: Iterable[str], tokens_b: Iterable[str]) -> float:
    """A4, Eq. 6."""
    tf_a, tf_b = term_frequencies(tokens_a), term_frequencies(tokens_b)
    return cosine(tf_a, tf_b)


CHARACTER_ALGORITHMS = {
    "levenshtein": levenshtein,
    "damerau_levenshtein": damerau_levenshtein,
    "jaro": jaro,
    "jaro_winkler": jaro_winkler,
    "smith_waterman": smith_waterman,
    "ngram": ngram_dice,
}
