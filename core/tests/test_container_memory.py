from datetime import datetime, timezone, timedelta
import json

import pytest

from hts_core.adapters.container_memory import cgroup_memory, effective_memory


def hierarchy(version=2, values=None):
    if version == 2:
        files = {'/proc/self/cgroup': '0::/team/job\n',
                 '/proc/self/mountinfo': '1 0 0:1 / /cg rw - cgroup2 cgroup rw\n'}
        names = ('memory.max', 'memory.current')
    else:
        files = {'/proc/self/cgroup': '3:memory:/team/job\n',
                 '/proc/self/mountinfo': '1 0 0:1 / /cg rw - cgroup cgroup rw,memory\n'}
        names = ('memory.limit_in_bytes', 'memory.usage_in_bytes')
    for directory, pair in zip(('/cg/team/job', '/cg/team', '/cg'),
                               values or [('1000', '200'), ('600', '500'), ('max', '700')], strict=True):
        for name, value in zip(names, pair, strict=True):
            files[directory+'/'+name] = value
    return lambda p: files[str(p)]


def test_parent_limit_and_vm_compete():
    groups = cgroup_memory(read=hierarchy())
    result = effective_memory(2000, 900, groups)
    assert result['available_bytes'] == 100
    assert result['total_bytes'] == 600
    assert effective_memory(2000, 50, groups)['available_bytes'] == 50


def test_v1_unlimited_and_exhausted_parent():
    groups = cgroup_memory(read=hierarchy(1, [('1000','100'), ('600','700'), (str(1 << 62),'900')]))
    assert groups['version'] == 1
    assert effective_memory(2000, 900, groups)['available_bytes'] == 0
    assert groups['visible_hierarchy'][-1]['limit_bytes'] is None


def test_unlimited_still_uses_vm():
    groups = cgroup_memory(read=hierarchy(values=[('max','200')]*3))
    assert effective_memory(2000, 900, groups)['available_bytes'] == 900


def test_missing_accounting_fails_closed():
    with pytest.raises((KeyError, OSError)):
        cgroup_memory(read=lambda p: '')


def test_host_minimum_and_freshness(tmp_path):
    groups = cgroup_memory(read=hierarchy())
    now = datetime.now(timezone.utc)
    host = tmp_path/'host.json'
    host.write_text(json.dumps({'utc':now.isoformat(), 'available_bytes':40}))
    assert effective_memory(2000,900,groups,host,now)['available_bytes'] == 40
    for offset in (-121, 10):
        host.write_text(json.dumps({'utc':(now+timedelta(seconds=offset)).isoformat(), 'available_bytes':40}))
        with pytest.raises(OSError, match='stale'):
            effective_memory(2000,900,groups,host,now)


def test_host_boolean_rejected(tmp_path):
    now = datetime.now(timezone.utc)
    host = tmp_path/'host.json'
    host.write_text(json.dumps({'utc':now.isoformat(), 'available_bytes':True}))
    with pytest.raises(OSError):
        effective_memory(2000,900,cgroup_memory(read=hierarchy()),host,now)


def test_non_root_mount_and_escaped_mountpoint():
    files = {'/proc/self/cgroup':'0::/docker/job',
             '/proc/self/mountinfo':r'1 0 0:1 /docker /cg\040memory rw - cgroup2 cgroup rw',
             '/cg memory/job/memory.max':'500', '/cg memory/job/memory.current':'400',
             '/cg memory/memory.max':'max', '/cg memory/memory.current':'700'}
    result = effective_memory(1000,800,cgroup_memory(read=lambda p:files[str(p)]))
    assert result['available_bytes'] == 100


@pytest.mark.parametrize('version', [1, 2])
def test_container_swap_limit_is_reported_without_hiding_unknown_ancestors(version):
    read = hierarchy(version)
    suffix = 'memory.swap.max' if version == 2 else 'memory.memsw.limit_in_bytes'
    def with_swap(path):
        if str(path) == '/cg/team/job/' + suffix:
            return '0' if version == 2 else '1000'
        return read(path)
    groups = cgroup_memory(read=with_swap)
    assert groups['visible_hierarchy'][0]['swap_limit_bytes'] == 0
    assert groups['visible_hierarchy'][1]['swap_limit_bytes'] is None


@pytest.mark.parametrize('version', [1, 2])
def test_headroom_counts_only_clean_inactive_file_cache_and_keeps_raw_usage(version):
    read = hierarchy(version)
    prefix = '' if version == 2 else 'total_'
    def with_cache(path):
        if str(path).endswith('/memory.stat'):
            names = ('inactive_file', 'file_dirty', 'file_writeback') if version == 2 else ('inactive_file', 'dirty', 'writeback')
            return '\n'.join(prefix+name+' '+str(value) for name, value in zip(names, (100, 20, 10), strict=True))
        return read(path)
    groups = cgroup_memory(read=with_cache)
    parent = groups['visible_hierarchy'][1]
    assert parent['headroom_bytes'] == 100
    assert parent['reclaimable_file_bytes'] == 70
    assert parent['available_headroom_bytes'] == 170
    assert effective_memory(2000, 900, groups)['available_bytes'] == 170
    assert effective_memory(2000, 50, groups)['available_bytes'] == 50
