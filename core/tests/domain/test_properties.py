import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from rapidfuzz.distance import OSA, Jaro, Levenshtein

from hts_core.domain import strings
from hts_core.domain.lexical import ReferenceIdf, cosine, idf_smooth
from hts_core.domain.metrics import average_ranks, pearson, spearman
from hts_core.domain.signature import salient_terms, signature, term_difference_by_term_count

text = st.text(alphabet="abcdeáçõ ", max_size=25)
tokens = st.lists(st.sampled_from(["casa", "rio", "pedra", "sol", "mar", "vento", "árvore"]), max_size=12)

SYMMETRIC = ["levenshtein", "damerau_levenshtein", "jaro", "smith_waterman", "ngram"]


@pytest.mark.parametrize("name", list(strings.CHARACTER_ALGORITHMS))
@given(a=text, b=text)
def test_character_algorithms_in_unit_interval(name, a, b):
    assert 0.0 <= strings.CHARACTER_ALGORITHMS[name](a, b) <= 1.0 + 1e-12


@pytest.mark.parametrize("name", list(strings.CHARACTER_ALGORITHMS))
@given(a=text)
def test_character_algorithms_identical_is_one(name, a):
    assert strings.CHARACTER_ALGORITHMS[name](a, a) == pytest.approx(1.0)


@pytest.mark.parametrize("name", SYMMETRIC)
@given(a=text, b=text)
def test_character_algorithms_symmetric(name, a, b):
    f = strings.CHARACTER_ALGORITHMS[name]
    assert f(a, b) == pytest.approx(f(b, a))


@given(a=text, b=text)
def test_jaro_winkler_symmetric_when_jaro_is(a, b):
    assert strings.jaro_winkler(a, b) == pytest.approx(strings.jaro_winkler(b, a))


@given(a=text)
def test_edit_distances_zero_for_equal_strings(a):
    assert strings.levenshtein_distance(a, a) == 0
    assert strings.damerau_levenshtein_distance(a, a) == 0


@given(a=text, b=text)
def test_levenshtein_matches_independent_implementation(a, b):
    assert strings.levenshtein_distance(a, b) == Levenshtein.distance(a, b)


@given(a=text, b=text)
def test_osa_matches_independent_implementation(a, b):
    assert strings.damerau_levenshtein_distance(a, b) == OSA.distance(a, b)


@given(a=text, b=text)
def test_jaro_matches_independent_implementation(a, b):
    # rapidfuzz usa t = floor(fora de ordem / 2); o mapa usa a metade exata. Só diverge com contagem ímpar.
    if a == b or not a or not b:
        assert strings.jaro(a, b) == pytest.approx(Jaro.similarity(a, b))
        return
    m, out_of_order = strings.jaro_counts(a, b)
    if out_of_order % 2 == 0:
        assert strings.jaro(a, b) == pytest.approx(Jaro.similarity(a, b))
    else:
        floored = (m / len(a) + m / len(b) + (m - out_of_order // 2) / m) / 3
        assert Jaro.similarity(a, b) == pytest.approx(floored)
        assert strings.jaro(a, b) < Jaro.similarity(a, b)


def test_jaro_odd_out_of_order_case_found_by_hypothesis():
    assert strings.jaro_counts("aab ", "a aaba") == (4, 3)
    assert strings.jaro("aab ", "a aaba") == pytest.approx((1 + 4 / 6 + 2.5 / 4) / 3)


@given(a=text, b=text)
def test_jaro_winkler_equals_jaro_when_first_char_differs(a, b):
    if a[:1] != b[:1]:
        assert strings.jaro_winkler(a, b) == strings.jaro(a, b)
    else:
        assert strings.jaro_winkler(a, b) >= strings.jaro(a, b)


def test_osa_counts_adjacent_transposition_as_one():
    assert strings.levenshtein_distance("ab", "ba") == 2
    assert strings.damerau_levenshtein_distance("ab", "ba") == 1


def test_smith_waterman_contained_substring_is_one():
    assert strings.smith_waterman("plágio", "detecção de plágio acadêmico") == 1.0


@given(a=tokens, b=tokens)
def test_vsm_cosine_symmetric_and_bounded(a, b):
    s = strings.vsm_cosine(a, b)
    assert 0.0 <= s <= 1.0 + 1e-12
    assert s == pytest.approx(strings.vsm_cosine(b, a))


REF = ReferenceIdf(n_docs=20, df={"casa": 15, "rio": 3, "pedra": 1, "sol": 20})


@given(a=tokens, b=tokens)
def test_tfidf_cosine_symmetric_and_bounded(a, b):
    s = cosine(REF.vector(a), REF.vector(b))
    assert 0.0 <= s <= 1.0 + 1e-12
    assert s == pytest.approx(cosine(REF.vector(b), REF.vector(a)))


@given(a=tokens.filter(bool))
def test_tfidf_cosine_identical_is_one(a):
    assert cosine(REF.vector(a), REF.vector(list(a))) == pytest.approx(1.0)


def test_smoothed_idf_never_zero_even_when_term_in_every_document():
    assert idf_smooth(2, 2) == pytest.approx(1.0)
    assert REF("sol") == pytest.approx(1.0)
    assert REF("desconhecido") == pytest.approx(math.log(21) + 1)
    assert REF("pedra") > REF("rio") > REF("casa") > REF("sol")


@given(a=tokens)
def test_signature_ignores_order_and_repetition(a):
    assert signature(a) == signature(list(reversed(a)) + a)


def test_signature_is_stable_across_processes_with_different_hash_seeds():
    code = "from hts_core.domain.signature import signature; print(signature(['plágio', 'sentença', 'índice']))"
    src = str(Path(__file__).resolve().parents[2] / "src")
    outputs = set()
    for seed in ("1", "2", "999"):
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": src}
        outputs.add(subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                   check=True).stdout.strip())
    assert len(outputs) == 1
    assert outputs.pop() == str(signature(["plágio", "sentença", "índice"]))


def test_term_difference_adaptation_is_directional():
    t1 = {"a", "b", "c", "d"}
    t2 = {"a", "b", "c", "d", "e", "f"}
    assert term_difference_by_term_count(t1, t2) == 0.5
    assert term_difference_by_term_count(t2, t1) == 0.0


def test_salient_terms_top_k_with_deterministic_ties():
    assert salient_terms({"b": 2.0, "a": 2.0, "c": 5.0, "z": 0.0}, k=3) == ["c", "a", "b"]


floats = st.lists(st.floats(-1e3, 1e3, allow_nan=False), min_size=3, max_size=30)


@given(x=floats, y=floats)
def test_pearson_matches_numpy(x, y):
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    assume(np.std(x) >= 1e-6 and np.std(y) >= 1e-6)
    assert pearson(x, y) == pytest.approx(float(np.corrcoef(x, y)[0, 1]), abs=1e-9)


def test_spearman_monotonic_is_one_and_handles_ties():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 1000]) == pytest.approx(1.0)
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert average_ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


@settings(max_examples=50)
@given(x=st.lists(st.integers(0, 10**6), min_size=3, max_size=20, unique=True))
def test_spearman_without_ties_equals_pearson_of_numpy_ranks(x):
    y = [v * v - 3 * v for v in reversed(x)]
    assume(len(set(y)) == len(y))
    rx = np.argsort(np.argsort(x)) + 1
    ry = np.argsort(np.argsort(y)) + 1
    assert spearman(x, y) == pytest.approx(float(np.corrcoef(rx, ry)[0, 1]), abs=1e-9)
