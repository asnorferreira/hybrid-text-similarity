import hashlib
import json
import os
from pathlib import Path

import pytest

from hts_core.adapters.semantic import cache_path
from tests.equivalence_support import STRONG, client_for, make_service, projection, strong_response
from tests.regression_support import PORTABILITY_POLICY, assert_frozen, assert_frozen_manifest

SNAPSHOT = Path(__file__).parent / 'fixtures/regression/q5v2-snapshot.json'


@pytest.fixture(scope='module')
def snapshot():
    data = json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    assert data['schema'] == 'hts-q5v2-regression-1'
    assert data['tolerance'] == {'absolute': 1e-9, 'relative': 0}
    assert data['research_dataset_used'] is False
    expected = [(case, kind, mode, relation) for case, kind, mode, relation in STRONG]
    actual = [(c['id'], c['format'], c['mode'], c['relation']) for c in data['cases']]
    assert actual == expected
    return data


@pytest.fixture(scope='module')
def service():
    return make_service()


@pytest.fixture(scope='module')
def observed():
    values = {}
    yield values
    if destination := os.environ.get('HTS_RG01_OBSERVED'):
        with Path(destination).open('x', encoding='utf-8') as stream:
            json.dump(values, stream, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            stream.write('\n')


@pytest.mark.parametrize('case,kind,mode,relation', STRONG, ids=[r[0] for r in STRONG])
def test_rg01_frozen_output(case, kind, mode, relation, snapshot, service, observed, record_property):
    expected = next(c['result'] for c in snapshot['cases'] if c['id'] == case)
    actual = projection(strong_response(client_for(service), kind, mode, relation))
    observed[case] = actual
    assert_frozen(actual, expected)
    record_property('regression_id', f'RG-01/{case}')
    record_property('snapshot_sha256', hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest())
    record_property('comparison_policy', PORTABILITY_POLICY)


def test_rg01_frozen_resources(snapshot, service):
    resources = snapshot['resources']
    assert service.encoder.identity == resources['model']
    assert_frozen_manifest((cache_path() / 'hts-model.json').read_bytes(), resources['model_manifest_sha256'])
    from hts_core.adapters.resource_migrations import verify_idf_header_migration
    verify_idf_header_migration(service.idf_info, resources['application_idf']['identity'])
    assert service.config['file_sha256'] == resources['policy_file_sha256']
    assert resources['research_training_idf_used'] is False


def test_rg01_detects_numeric_and_class_drift():
    with pytest.raises(AssertionError):
        assert_frozen({'index': .5 + 2e-9}, {'index': .5})
    with pytest.raises(AssertionError):
        assert_frozen({'label': 'parafrase'}, {'label': 'copia_exata'})
    assert_frozen({'index': .5 + .5e-9}, {'index': .5})
