"""RG-01 portability policy; historical snapshots are never regenerated here."""

import hashlib
import math
import re

import pytest

STRICT_ABSOLUTE = 1e-9
# The Transformer emits float32 embeddings. CPU kernels need not be bitwise
# identical. One float32 epsilon is the explicit score-space acceptance budget,
# not a promise that every future backend will meet it. Larger drift still fails.
SEMANTIC_ABSOLUTE = 2.0 ** -23
FUSION_WEIGHT = 0.6
PORTABILITY_POLICY = 'rg01-cpu-float32-1; semantic=2^-23; fusion=0.6; percent=100; rel=0'


def numeric_tolerance(path, expected):
    """Propagate only the semantic budget through Q5-v2's fixed formulas."""
    if expected.get('method') != 'hybrid':
        return STRICT_ABSOLUTE
    budget = STRICT_ABSOLUTE
    if re.fullmatch(r'result\.(?:matches\[\d+\]\.(?:semantic_raw|semantic_operational)|'
                    r'matrices\.(?:semantic_raw|semantic_operational)\[\d+\]\[\d+\])', path):
        budget = SEMANTIC_ABSOLUTE
    elif re.fullmatch(r'result\.(?:matches\[\d+\]\.fused|matrices\.fused\[\d+\]\[\d+\]|'
                      r'alignment\.pairs\[\d+\]\.score)', path):
        budget = FUSION_WEIGHT * SEMANTIC_ABSOLUTE
    elif path == 'result.alignment.objective':
        budget = len(expected['alignment']['pairs']) * FUSION_WEIGHT * SEMANTIC_ABSOLUTE
    elif re.fullmatch(r'result\.(?:index|semantic_index)\.(?:value|source_to_suspect|suspect_to_source)', path):
        budget = SEMANTIC_ABSOLUTE
        if path.startswith('result.index.'):
            budget *= FUSION_WEIGHT
        if path.endswith('.value'):
            budget *= 100
    return max(STRICT_ABSOLUTE, budget)


def assert_frozen(actual, expected, path='result', *, root=None):
    root = expected if root is None and isinstance(expected, dict) else root
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and actual.keys() == expected.keys(), path
        for key in expected:
            assert_frozen(actual[key], expected[key], f'{path}.{key}', root=root)
    elif isinstance(expected, list):
        assert isinstance(actual, list) and len(actual) == len(expected), path
        for i, (a, b) in enumerate(zip(actual, expected, strict=True)):
            assert_frozen(a, b, f'{path}[{i}]', root=root)
    elif isinstance(expected, float):
        assert type(actual) is float and math.isfinite(actual) and math.isfinite(expected), path
        tolerance = numeric_tolerance(path, root or {})
        assert actual == pytest.approx(expected, abs=tolerance, rel=0), f'{path}; abs={tolerance}'
    else:
        assert type(actual) is type(expected), path
        assert actual == expected, path


def assert_frozen_manifest(payload, expected_sha256):
    """Match the pinned bytes allowing only uniform LF versus CRLF conversion."""
    if hashlib.sha256(payload).hexdigest() == expected_sha256:
        return
    lf = payload.replace(b'\r\n', b'\n')
    # Do not silently normalize mixed endings, bare CR, JSON formatting or keys.
    assert b'\r' not in lf, 'bare CR in model manifest'
    assert payload in (lf, lf.replace(b'\n', b'\r\n')), 'mixed model manifest line endings'
    assert expected_sha256 in {
        hashlib.sha256(lf).hexdigest(),
        hashlib.sha256(lf.replace(b'\n', b'\r\n')).hexdigest(),
    }, 'model manifest differs beyond uniform LF/CRLF'
