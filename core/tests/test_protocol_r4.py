import copy
from pathlib import Path

import pytest

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.training_contract import readiness, validate_s5b

ROOT = Path(__file__).resolve().parents[1]


def protocol():
    return read_json(ROOT / 'configs/experiment_s5b.r4.json')


def examples():
    return {split: [{'target': index % 3 / 2} for index in range(20)] for split in ('train', 'validation')}


def snapshot(available=1_800_000_000, limit=2_000_000_000, swap=0):
    return {'available_bytes': available, 'cgroup': {'visible_hierarchy': [
        {'limit_bytes': limit, 'swap_limit_bytes': swap}]}}


def test_resource_revision_preserves_scientific_design_and_old_protocol_identities():
    old = read_json(ROOT / 'configs/experiment_s5b.r3.json')
    new = protocol()
    assert validate_s5b(old) == 'b8137660098a04d63ff11500ce4d3c2c23f7fd2dee23bb7fb3020ca77a5996cc'
    assert len(validate_s5b(new)) == 64
    changed = {'schema', 'adopted_utc', 'authorization', 'budget', 'readiness', 'resource_policy'}
    assert {k: v for k, v in old.items() if k not in changed} == {k: v for k, v in new.items() if k not in changed}
    assert {k: v for k, v in old['budget'].items() if k != 'process_rss_limit_bytes'} == {
        k: v for k, v in new['budget'].items() if k != 'process_rss_limit_bytes'}


@pytest.mark.parametrize('available,released', [(1_799_999_999, False), (1_800_000_000, True)])
def test_headroom_is_required_even_under_a_hard_memory_cap(available, released):
    report = readiness(protocol(), 'H2', examples(), snapshot(available))
    assert report['releasable'] == released
    assert report['required_available_bytes'] == 1_800_000_000
    assert report['final_test_allowed'] is False


@pytest.mark.parametrize('limit', [None, 1_500_000_000, 2_000_000_001, 2_147_483_648, 4_000_000_000])
def test_h2_refuses_a_missing_or_different_container_budget(limit):
    report = readiness(protocol(), 'H2', examples(), snapshot(limit=limit))
    assert not report['releasable']
    assert report['blockers'] == ['H2_requires_adopted_2GB_container_memory_limit']


def test_kernel_page_rounding_does_not_increase_the_adopted_memory_cap():
    import os
    page_size = os.sysconf('SC_PAGE_SIZE') if hasattr(os, 'sysconf') else 4096
    rounded = 2_000_000_000-2_000_000_000 % page_size
    assert readiness(protocol(), 'H2', examples(), snapshot(limit=rounded))['releasable']
    assert not readiness(protocol(), 'H2', examples(), snapshot(limit=rounded-page_size))['releasable']


def test_h2_checks_the_smallest_exposed_cgroup_limit():
    memory = snapshot()
    memory['cgroup']['visible_hierarchy'].append({'limit_bytes': 1_000_000_000})
    assert not readiness(protocol(), 'H2', examples(), memory)['releasable']
    assert not readiness(protocol(), 'H2', examples(), {'available_bytes': 4_000_000_000})['releasable']


@pytest.mark.parametrize('swap', [None, 1_000_000_000])
def test_missing_or_enabled_swap_blocks_the_resource_revision(swap):
    report = readiness(protocol(), 'H2', examples(), snapshot(swap=swap))
    assert not report['releasable']
    assert report['blockers'] == ['H2_requires_zero_container_swap']


@pytest.mark.parametrize('path,value', [
    (('siamese', 'encoder_trainable'), True),
    (('siamese', 'trainable_parameter_count'), 1),
    (('budget', 'maximum_epochs'), 1),
    (('readiness', 'training_free_memory_bytes'), 1_000_000_000),
    (('resource_policy', 'container_memory_swap_bytes'), 4_000_000_000),
    (('resource_policy', 'checkpoint_read_chunk_bytes'), 32_000_000),
])
def test_resource_revision_refuses_unapproved_changes(path, value):
    value_config = copy.deepcopy(protocol())
    value_config[path[0]][path[1]] = value
    with pytest.raises(ValueError):
        validate_s5b(value_config)


def test_resource_revision_cannot_open_the_test_split():
    with pytest.raises(PermissionError):
        readiness(protocol(), 'H2', {'train': [], 'test': []}, snapshot())
