import numpy as np
import pytest

from hts_core.domain.lexical import a1_tfidf_vectors, cosine, idf_smooth
from hts_core.domain.strings import char_ngrams, jaro_winkler, vsm_cosine
from hts_core.domain.text import clean_extracted
from hts_core.domain.signature import a3_relation, term_difference, term_difference_by_term_count
from hts_core.domain.vectors import alignment_similarity, cosine_dense


def test_zero_norm_policy_for_all_cosines():
    for a, b in [({}, {}), ({"a": 0.0}, {"a": 1.0})]:
        assert cosine(a, b) == 0.0
    assert vsm_cosine([], []) == 0.0
    assert vsm_cosine(["a"], []) == 0.0
    assert cosine_dense(np.zeros(2), np.ones(2)) == 0.0
    assert alignment_similarity(np.zeros(2), np.ones(2)) == 1.0
    vectors = a1_tfidf_vectors({"a": ["igual"], "b": ["igual"]})
    assert vectors == {"a": {"igual": 0.0}, "b": {"igual": 0.0}}
    assert cosine(vectors["a"], vectors["b"]) == 0.0


def test_general_cosine_can_be_negative_and_alignment_can_be_zero():
    assert cosine({"x": -1}, {"x": 1}) == -1.0
    assert cosine_dense(np.array([-1.0]), np.array([1.0])) == -1.0
    assert alignment_similarity(np.array([-1.0]), np.array([1.0])) == 0.0


@pytest.mark.parametrize("word", ["guarda-chuva", "segunda-feira", "bem-estar", "fazê-lo"])
def test_recognized_compounds_survive_line_break(word):
    assert clean_extracted(word.replace("-", "-\n")) == word
    assert clean_extracted(word) == word


def test_shingles_preserve_internal_order_before_set_comparison():
    assert char_ngrams("abcd", 2) == {"ab", "bc", "cd"}
    assert char_ngrams("dcba", 2) == {"dc", "cb", "ba"}


def test_directional_term_difference_can_exceed_one():
    assert term_difference_by_term_count(["a"], ["b", "c", "d"]) == 3.0
    assert term_difference_by_term_count(["b", "c", "d"], ["a"]) == 1.0


def test_a3_denominator_uses_terms_of_document_smaller_by_size():
    a, b = {"a", "b", "c", "d"}, {"a", "b", "e"}
    assert term_difference(a, b, 100, 200, direction="doc2_minus_doc1") == 1 / 4
    assert term_difference(a, b, 100, 200, direction="doc1_minus_doc2") == 2 / 4
    assert term_difference(a, b, 200, 100, direction="doc2_minus_doc1") == 1 / 3
    assert term_difference_by_term_count(a, b) == 1 / 3


def test_a3_reference_refuses_unresolved_ties_empty_denominator_and_implicit_direction():
    with pytest.raises(ValueError, match="desempate"):
        term_difference(["a"], ["a", "b"], 100, 100, direction="doc1_minus_doc2")
    with pytest.raises(ValueError, match="denominador vazio"):
        term_difference([], ["a"], 0, 1, direction="doc1_minus_doc2")
    with pytest.raises(TypeError):
        term_difference(["a"], ["b"], 100, 200)


@pytest.mark.parametrize("delta,size,result", [(.099, 110, "muito_similar"), (.1, 110, "relacionado"),
                                             (.199, 200, "relacionado"), (.2, 150, "texto_inserido"),
                                             (.5, 150, "distinto"), (.2, 151, "distinto")])
def test_a3_project_labels_and_threshold_boundaries(delta, size, result):
    assert a3_relation(delta, 100, size) == result


@pytest.mark.parametrize("n,df", [(0, 1), (2, 3), (-1, 0), (2, -1)])
def test_smoothed_idf_rejects_impossible_document_frequencies(n, df):
    with pytest.raises(ValueError):
        idf_smooth(n, df)


def test_invalid_string_parameters_are_explicit():
    with pytest.raises(ValueError):
        jaro_winkler("a", "a", p=0.3)
    with pytest.raises(ValueError):
        char_ngrams("abc", n=0)
