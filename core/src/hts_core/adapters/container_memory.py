from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import re


def _unescape(value):
    return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), value)


def cgroup_memory(proc=Path('/proc'), read=lambda p: p.read_text()):
    memberships = [line.split(':', 2) for line in read(proc/'self/cgroup').splitlines()]
    mounts = [line.split() for line in read(proc/'self/mountinfo').splitlines()]
    candidates = []
    for mount in mounts:
        sep = mount.index('-')
        kind = mount[sep+1]
        for _, controllers, member in memberships:
            if ((kind == 'cgroup2' and controllers == '') or
                (kind == 'cgroup' and 'memory' in controllers.split(',') and
                 'memory' in mount[sep+3].split(','))):
                candidates.append((kind, _unescape(mount[3]), _unescape(mount[4]), member))
    if len(candidates) != 1:
        raise OSError('cannot resolve a unique memory cgroup hierarchy')
    kind, root, point, member = candidates[0]
    try:
        relative = PurePosixPath(member).relative_to(root)
    except ValueError as exc:
        raise OSError('memory cgroup is outside visible mount root') from exc
    if '..' in relative.parts:
        raise OSError('invalid cgroup membership')
    mount = Path(point)
    current = mount.joinpath(*relative.parts)
    records = []
    while True:
        limit_file, usage_file = ('memory.max', 'memory.current') if kind == 'cgroup2' else ('memory.limit_in_bytes', 'memory.usage_in_bytes')
        raw_limit = read(current/limit_file).strip()
        usage = int(read(current/usage_file).strip())
        limit = None if raw_limit == 'max' else int(raw_limit)
        if kind == 'cgroup' and limit is not None and limit >= (1 << 60):
            limit = None
        if usage < 0 or (limit is not None and limit < 0):
            raise OSError('invalid cgroup memory accounting')
        records.append({'path': str(current), 'limit_bytes': limit, 'current_bytes': usage,
                        'headroom_bytes': None if limit is None else max(0, limit-usage)})
        if current == mount:
            break
        current = current.parent
    return {'version': 2 if kind == 'cgroup2' else 1, 'visible_hierarchy': records,
            'scope': 'all exposed ancestors; ancestors hidden by cgroup namespace are not observable'}


def effective_memory(total, available, cgroup, host_file=None, now=None):
    limits = [r['limit_bytes'] for r in cgroup['visible_hierarchy'] if r['limit_bytes'] is not None]
    headroom = [r['headroom_bytes'] for r in cgroup['visible_hierarchy'] if r['headroom_bytes'] is not None]
    result = {'vm_total_bytes': total, 'vm_available_bytes': available, 'cgroup': cgroup,
              'total_bytes': min([total]+limits), 'available_bytes': min([available]+headroom)}
    if host_file is not None:
        host = json.loads(Path(host_file).read_text(encoding='utf-8-sig'))
        timestamp = datetime.fromisoformat(host['utc'])
        if timestamp.utcoffset() is None:
            raise OSError('host memory timestamp requires timezone')
        age = ((now or datetime.now(timezone.utc))-timestamp).total_seconds()
        value = host['available_bytes']
        if type(value) is not int or value < 0 or not 0 <= age <= 120:
            raise OSError('invalid or stale host memory snapshot')
        result['host'] = host
        result['available_bytes'] = min(result['available_bytes'], value)
    return result
