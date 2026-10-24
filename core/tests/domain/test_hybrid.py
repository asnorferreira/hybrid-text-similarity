from fractions import Fraction
from itertools import permutations

from hypothesis import given, strategies as st
import numpy as np
import pytest
from scipy.optimize import linear_sum_assignment

from hts_core.domain.hybrid import (bounded, class_summary, classify_pair, content_windows, fuse, hungarian,
                                    operational_cosine, pool_windows, semantic_cosine, similarity_index)
from hts_core.domain.strings import levenshtein


@pytest.mark.parametrize('other,expected', [([1, 0], 1), ([0, 1], 0), ([-1, 0], -1)])
def test_semantic_reference_vectors(other, expected):
    raw = semantic_cosine([1, 0], other)
    assert raw == expected
    assert operational_cosine(raw) == max(0, expected)


@pytest.mark.parametrize('vector', [[0, 0], [float('nan'), 1], [float('inf'), 1], []])
def test_invalid_semantic_vectors_have_no_cosine(vector):
    with pytest.raises(ValueError):
        semantic_cosine(vector, [1, 0])


def test_roundoff_policy_is_small_and_explicit():
    assert bounded(1 + 5e-13) == 1
    for value in [1 + 2e-12, -2e-12, float('nan'), float('inf')]:
        with pytest.raises(ValueError):
            bounded(value)


def test_fusion_fraction_oracle_and_negative_raw():
    operational, matrix = fuse([[.5, 0]], [[.75, -.5]])
    assert matrix[0, 0] == pytest.approx(float(Fraction(3, 5) * Fraction(3, 4) + Fraction(2, 5) * Fraction(1, 2)))
    assert operational.tolist() == [[.75, 0]]
    assert matrix[0, 1] == 0
    with pytest.raises(ValueError):
        fuse([[1]], [[1, 0]])


def test_index_contraproof_and_zero_lexical_no_identity_shortcut():
    result = similarity_index([[1, 0]], [1], [1, 1])
    assert result == {'source_to_suspect': 1, 'suspect_to_source': .5, 'value': 75}
    _, f = fuse([[0]], [[1]])
    assert similarity_index(f, [1], [1])['value'] == 60


@pytest.mark.parametrize('matrix,a,b', [([], [], []), ([[1]], [0], [1]), ([[1]], [-1], [1]), ([[1]], [float('nan')], [1]), ([[1]], [1, 1], [1])])
def test_index_invalid_inputs(matrix, a, b):
    with pytest.raises(ValueError):
        similarity_index(matrix, a, b)


@given(st.lists(st.lists(st.integers(0, 100), min_size=3, max_size=3), min_size=2, max_size=2))
def test_index_symmetry_and_matching_against_enumeration(values):
    matrix = np.asarray(values) / 100
    a = similarity_index(matrix, [1, 2], [3, 1, 2])
    b = similarity_index(matrix.T, [3, 1, 2], [1, 2])
    assert a['value'] == pytest.approx(b['value'])
    assert a['source_to_suspect'] == b['suspect_to_source']
    expected = max(sum(matrix[i, j] for i, j in enumerate(order)) for order in permutations(range(3), 2))
    actual = hungarian(matrix)
    assert actual['objective'] == pytest.approx(expected)
    rows, cols = linear_sum_assignment(matrix, maximize=True)
    assert actual['objective'] == pytest.approx(sum(matrix[rows, cols]))


def test_hungarian_cross_pair_is_separate_from_best_pair_index():
    matrix = [[.9, .8], [.85, 0]]
    result = hungarian(matrix)
    assert [(p['source'], p['suspect']) for p in result['pairs']] == [(0, 1), (1, 0)]
    assert result['objective'] == pytest.approx(float(Fraction(33, 20)))
    assert similarity_index(matrix, [1, 1], [1, 1])['value'] == pytest.approx(86.25)


def test_hungarian_zero_rectangular_and_deterministic_ties():
    assert hungarian([[0, 0]]) == {'pairs': [], 'unmatched_source': [0], 'unmatched_suspect': [0, 1], 'objective': 0}
    assert hungarian([[1], [0]])['unmatched_source'] == [1]
    expected = [{'source': 0, 'suspect': 0, 'score': 1.}, {'source': 1, 'suspect': 1, 'score': 1.}]
    assert hungarian([[1, 1], [1, 1]])['pairs'] == expected
    assert hungarian([[1, 1], [1, 1]])['pairs'] == expected


@pytest.mark.parametrize('lexical,semantic,edit,label,reason', [
    (.9, .9, .85, 'copia_editada', 'semelhanca_estrutural'),
    (.1, .2, .8, 'copia_editada', 'semelhanca_estrutural'),
    (.2, .3, .799999, 'sem_correspondencia_detectada', 'escores_baixos_sem_evidencia_estrutural'),
    (.2, .75, .4, 'sem_correspondencia_detectada', 'evidencia_insuficiente_pelas_regras'),
    (.2, .750001, .4, 'parafrase', 'similaridade_semantica_operacional'),
    (.95, .5, .4, 'sem_correspondencia_detectada', 'evidencia_insuficiente_pelas_regras'),
])
def test_v2_independent_features_at_boundaries(lexical, semantic, edit, label, reason):
    result = classify_pair('texto A', 'outro B', lexical, semantic, edit)
    assert result['label'] == label
    assert result['reason'] == reason
    assert result['lexical_high'] == (lexical > .85)


def test_v2_actual_character_boundary_and_sensitive_case():
    assert levenshtein('abcde', 'abcdX') == .8
    assert classify_pair('abcde', 'abcdX', .1, .2, levenshtein('abcde', 'abcdX'))['label'] == 'copia_editada'
    assert classify_pair('Texto', 'Texto', 0, 1, 1)['label'] == 'copia_exata'
    assert classify_pair('Texto', 'texto', 1, 1, .8)['label'] == 'copia_editada'
    with pytest.raises(ValueError):
        classify_pair('', '', 1, 1, 1)
    with pytest.raises(ValueError):
        classify_pair('a', 'b', 1, float('nan'), 0)


def test_distribution_tie_and_inserted_unavailable():
    result = class_summary(['copia_exata', 'parafrase'])
    assert result['counts']['copia_exata'] == 1
    assert result['proportions']['parafrase'] == .5
    assert result['denominator'] == 2
    assert result['predominance'] == 'sem_predominancia'
    assert result['inserted_segment'] == 'indisponivel_regra_nao_definida'


def test_window_coverage_pooling_and_cancellation():
    ids = list(range(253))
    chunks = content_windows(ids, 126)
    assert [len(c) for c in chunks] == [126, 126, 1]
    assert [token for chunk in chunks for token in chunk] == ids
    assert chunks[-1] == [252]
    np.testing.assert_allclose(pool_windows([[2, 0], [0, 3]], [3, 4]), [.6, .8])
    np.testing.assert_allclose(pool_windows([[3, 4]], [7]), [.6, .8])
    with pytest.raises(ValueError):
        pool_windows([[1, 0], [-1, 0]], [1, 1])
