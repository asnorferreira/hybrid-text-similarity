import copy
from pathlib import Path

import pytest

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.training_contract import readiness, validate_s5b

ROOT = Path(__file__).resolve().parents[1]


def protocol():
    return read_json(ROOT / 'configs/experiment_s5b.r3.json')


def test_both_adopted_revisions_validate():
    old = read_json(ROOT / 'configs/experiment_s5b.json')
    assert validate_s5b(old) == '1bc0736e297e6cd97029db68553d3f1c9825955120005a2b2a3ef9f10ca541d0'
    assert validate_s5b(protocol()) == identity(protocol())
    assert protocol()['readiness'] == old['readiness']
    assert protocol()['budget'] == old['budget']


@pytest.mark.parametrize('change', ['extra', 'test', 'feature', 'encoder', 'parameter', 'reserve'])
def test_r3_refuses_unapproved_changes(change):
    value = copy.deepcopy(protocol())
    if change == 'extra': value['extra'] = 1
    elif change == 'test': value['allowed_splits'] = ['train', 'test']
    elif change == 'feature': value['h1']['features_by_system']['learned_fusion'] = ['r', 'origin']
    elif change == 'encoder': value['siamese']['encoder_trainable'] = True
    elif change == 'parameter': value['siamese']['trainable_parameter_count'] = 1
    else: value['readiness']['training_free_memory_bytes'] = 1024**3
    with pytest.raises(ValueError): validate_s5b(value)


def test_r3_does_not_open_test_or_lower_resource_gate():
    with pytest.raises(PermissionError): readiness(protocol(), 'H2', {'train': [], 'test': []}, {'available_bytes': 8*1024**3})
    rows = {s: [{'target': i % 3 / 2} for i in range(20)] for s in ('train', 'validation')}
    result = readiness(protocol(), 'H2', rows, {'available_bytes': 3*1024**3})
    assert not result['releasable']
    assert result['required_available_bytes'] == 4*1024**3
