from datetime import datetime
import math
import os
from pathlib import Path
import sys

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.contract_types import text
from hts_core.domain.experiments import require_split

SCHEMA = Path(__file__).resolve().parents[3]/'configs/experiment_s5b.schema.json'


def validate_s5b(config):
    def visit(value, schema, path):
        kind = schema['type']
        types = {'object': dict, 'array': list, 'string': str, 'boolean': bool, 'integer': int, 'null': type(None)}
        valid = type(value) in (int, float) and math.isfinite(value) if kind == 'number' else type(value) is types[kind]
        if not valid:
            raise ValueError(path+': invalid type or nonfinite value')
        if kind == 'object':
            if set(value) != set(schema['required']):
                raise ValueError(path+': missing or unknown fields')
            for key, item in value.items():
                visit(item, schema['properties'][key], path+'.'+key)
        elif kind == 'array':
            if len(value) != schema['minItems']:
                raise ValueError(path+': array length differs from adopted profile')
            for i, (item, spec) in enumerate(zip(value, schema['prefixItems'], strict=True)):
                visit(item, spec, f'{path}[{i}]')
        elif 'const' in schema and value != schema['const']:
            raise ValueError(path+': unsupported value for adopted revision')
        elif kind == 'string':
            text(value, path)
    schema = read_json(SCHEMA)
    if 'oneOf' in schema:
        profiles = {item['properties']['schema']['const']: item for item in schema['oneOf']}
        try:
            schema = profiles[config['schema']]
        except (KeyError, TypeError) as exc:
            raise ValueError('unsupported S5B revision') from exc
    visit(config, schema, 's5b')
    if datetime.fromisoformat(config['adopted_utc']).utcoffset() is None:
        raise ValueError('adoption timestamp requires timezone')
    return identity(config)


def memory_snapshot():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes

        class Memory(ctypes.Structure):
            _fields_ = [('length', wintypes.DWORD), ('load', wintypes.DWORD)] + [
                (k, ctypes.c_ulonglong) for k in ('total', 'available', 'page_total', 'page_available', 'virtual_total', 'virtual_available', 'extended')]

        class Counters(ctypes.Structure):
            _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
                (k, ctypes.c_size_t) for k in ('peak_ws', 'ws', 'peak_page_pool', 'page_pool', 'peak_nonpage_pool', 'nonpage_pool', 'pagefile', 'peak_pagefile')]

        m = Memory(); m.length = ctypes.sizeof(m)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)):
            raise OSError('GlobalMemoryStatusEx failed')
        c = Counters(); c.cb = ctypes.sizeof(c)
        get_process = ctypes.windll.kernel32.GetCurrentProcess
        get_process.restype = wintypes.HANDLE
        query = ctypes.windll.psapi.GetProcessMemoryInfo
        query.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
        if not query(get_process(), ctypes.byref(c), c.cb):
            raise OSError('GetProcessMemoryInfo failed')
        return {'total_bytes': m.total, 'available_bytes': m.available, 'rss_bytes': c.ws, 'peak_rss_bytes': c.peak_ws,
                'scope': 'Windows physical available; working set including native allocations; no GPU accounting'}
    values = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
    rss = int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
    from hts_core.adapters.container_memory import cgroup_memory, effective_memory
    result = effective_memory(int(values['MemTotal'].split()[0])*1024,
                              int(values['MemAvailable'].split()[0])*1024, cgroup_memory(),
                              os.environ.get('HTS_HOST_MEMORY_SNAPSHOT'))
    result.update(rss_bytes=rss, peak_rss_bytes=None,
                  scope='minimum of Linux VM MemAvailable, exposed cgroup headroom and supplied fresh host availability; RSS includes native resident pages; no GPU accounting')
    return result


def readiness(config, task, examples, snapshot):
    protocol_id = validate_s5b(config)
    if task not in ('H1','H2') or set(examples) != {'train','validation'}:
        raise PermissionError('S5B accepts H1/H2 and train/validation only')
    blockers = []
    targets = {}
    minimum = config['readiness']
    for split, rows in examples.items():
        require_split(split)
        targets[split] = [r['target'] for r in rows]
        if task == 'H1':
            threshold = minimum['minimum_'+split+'_per_class']
            for label in config['h1']['classes']:
                if targets[split].count(label) < threshold:
                    blockers.append(f'{split}: insufficient {label}')
        elif (len(rows) < minimum['minimum_h2_'+split] or
              len(set(targets[split])) < minimum['minimum_distinct_h2_targets']):
            blockers.append(split+': insufficient H2 targets/diversity')
    gate = 'training_free_memory_bytes' if task == 'H2' else 'inference_free_memory_bytes'
    if snapshot['available_bytes'] < minimum[gate]:
        blockers.append('available_physical_memory_below_adopted_'+gate)
    return {'protocol_identity': protocol_id, 'task': task, 'scope': 'exploratory_against_dependent_automated_reference',
            'eligible_counts': {s:len(v) for s,v in examples.items()}, 'resources':snapshot,
            'required_available_bytes':minimum[gate], 'blockers':blockers, 'releasable':not blockers,
            'independent_gold':False, 'final_test_allowed':False}
