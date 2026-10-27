import copy
import hashlib
import json
from pathlib import Path

import pytest

from tests.regression_support import (
    FUSION_WEIGHT,
    SEMANTIC_ABSOLUTE,
    STRICT_ABSOLUTE,
    assert_frozen,
    assert_frozen_manifest,
    numeric_tolerance,
)


SNAPSHOT = Path(__file__).parent / 'fixtures/regression/q5v2-snapshot.json'


@pytest.mark.parametrize('path,expected_budget', [
    ('result.matches[0].semantic_raw', SEMANTIC_ABSOLUTE),
    ('result.matches[12].semantic_operational', SEMANTIC_ABSOLUTE),
    ('result.matrices.semantic_raw[0][0]', SEMANTIC_ABSOLUTE),
    ('result.matrices.semantic_operational[0][0]', SEMANTIC_ABSOLUTE),
    ('result.matches[0].fused', FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.matrices.fused[1][2]', FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.alignment.pairs[0].score', FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.alignment.objective', 2 * FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.index.source_to_suspect', FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.index.suspect_to_source', FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.index.value', 100 * FUSION_WEIGHT * SEMANTIC_ABSOLUTE),
    ('result.semantic_index.source_to_suspect', SEMANTIC_ABSOLUTE),
    ('result.semantic_index.suspect_to_source', SEMANTIC_ABSOLUTE),
    ('result.semantic_index.value', 100 * SEMANTIC_ABSOLUTE),
])
def test_semantic_tolerance_is_explicit_scaled_and_bounded(path, expected_budget):
    root = {'method': 'hybrid', 'alignment': {'pairs': [{}, {}]}}
    assert numeric_tolerance(path, root) == expected_budget
    assert_frozen(.5 + expected_budget / 2, .5, path, root=root)
    with pytest.raises(AssertionError):
        assert_frozen(.5 + expected_budget * 2, .5, path, root=root)
    assert numeric_tolerance(path, {**root, 'method': 'lexical'}) == STRICT_ABSOLUTE


@pytest.mark.parametrize('path', [
    'result.lexical_index.value', 'result.matrices.lexical[0][0]',
    'result.matches[0].lexical', 'result.matches[0].edit',
    'result.matches[0].characters.vsm_cosine', 'result.summary.proportions.parafrase',
    'result.index.unknown', 'result.semantic_index.unknown',
    'result.source[0].semantic_raw', 'result.unknown.semantic_raw',
])
def test_lexical_and_unknown_fields_keep_original_strict_tolerance(path):
    root = {'method': 'hybrid'}
    assert numeric_tolerance(path, root) == STRICT_ABSOLUTE
    with pytest.raises(AssertionError):
        assert_frozen(.5 + 2e-9, .5, path, root=root)


@pytest.mark.parametrize('actual,expected', [
    (float('nan'), .5), (float('inf'), .5), (float('-inf'), .5),
    (float('nan'), float('nan')), (True, 1.), (1, 1.),
])
def test_nonfinite_or_wrong_numeric_type_fails(actual, expected):
    with pytest.raises(AssertionError):
        assert_frozen(actual, expected, 'result.matches[0].semantic_raw', root={'method': 'hybrid'})


def test_real_ci_deltas_accepted_without_changing_frozen_expected():
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    # First failing leaves copied from job 122015196243, not recomputed targets.
    observations = {
        'NFo-02': ('objective', 0.9906188793535291),
        'NFo-03': ('objective', 0.9758130736400638),
        'NFo-04': ('semantic_raw', -0.07725675163269038),
    }
    for case in data['cases']:
        if case['id'] not in observations:
            continue
        expected = case['result']
        actual = copy.deepcopy(expected)
        field, value = observations[case['id']]
        if field == 'objective':
            actual['alignment'][field] = value
        else:
            actual['matches'][0][field] = value
        assert_frozen(actual, expected)


@pytest.mark.parametrize('change', ['label', 'selection', 'count', 'matrix_shape', 'new_field'])
def test_semantic_budget_keeps_decisions_structure_and_selection_exact(change):
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    expected = data['cases'][1]['result']
    actual = copy.deepcopy(expected)
    if change == 'label':
        actual['matches'][0]['decision']['label'] = 'parafrase'
    elif change == 'selection':
        actual['alignment']['pairs'][0]['source'] = 1
    elif change == 'count':
        actual['summary']['counts']['parafrase'] += 1
    elif change == 'matrix_shape':
        actual['matrices']['semantic_raw'][0].append(.9)
    else:
        actual['unknown'] = .5
    with pytest.raises(AssertionError):
        assert_frozen(actual, expected)


def test_relative_tolerance_remains_zero():
    with pytest.raises(AssertionError):
        assert_frozen(1000000000.01, 1000000000., 'result.semantic_index.value', root={'method': 'hybrid'})


@pytest.mark.parametrize('expected_ending', [b'\n', b'\r\n'])
@pytest.mark.parametrize('actual_ending', [b'\n', b'\r\n'])
def test_only_uniform_lf_crlf_conversion_is_allowed(expected_ending, actual_ending):
    payload = b'{\n  "model": "pinned",\n  "files": {}\n}'
    expected = hashlib.sha256(payload.replace(b'\n', expected_ending)).hexdigest()
    assert_frozen_manifest(payload.replace(b'\n', actual_ending), expected)


@pytest.mark.parametrize('altered', [
    b'{\n "model": "pinned",\n  "files": {}\n}',
    b'{\n  "model": "changed",\n  "files": {}\n}',
    b'{\n  "model": "pinned",\n  "files": {"x":"altered"}\n}',
    b'{\n  "model": "pinned",\r\n  "files": {}\n}',
    b'{\r  "model": "pinned",\r  "files": {}\r}',
    b'{\n  "model": "pinned",\n  "files": {}\n}\n',
])
def test_manifest_content_formatting_mixed_endings_and_extra_newline_fail(altered):
    expected = hashlib.sha256(b'{\n  "model": "pinned",\n  "files": {}\n}').hexdigest()
    with pytest.raises(AssertionError):
        assert_frozen_manifest(altered, expected)
