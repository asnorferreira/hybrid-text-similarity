import copy
import hashlib
import json
from pathlib import Path

from hts_core.adapters.dataset_store import read_json


def verify_idf_header_migration(descriptor, historical_identity):
    core = Path(__file__).resolve().parents[3]
    migration = read_json(core/'assets/calibration/rg01-header-migration.json')
    source = (core/migration['source']).read_bytes()
    if (hashlib.sha256(source).hexdigest() != migration['after_sha256'] or
        hashlib.sha256(migration['removed_prefix'].encode()+source).hexdigest() != migration['before_sha256']):
        raise ValueError('RG01 header migration source differs')
    def identity(value):
        return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    current = {k:v for k,v in descriptor.items() if k!='identity'}
    if descriptor['identity'] != identity(current):
        raise ValueError('RG01 descriptor identity differs')
    historical = copy.deepcopy(current)
    if historical['observed_pipeline'][migration['source']] != migration['after_sha256']:
        raise ValueError('RG01 observed source differs')
    historical['observed_pipeline'][migration['source']] = migration['before_sha256']
    if identity(historical) != historical_identity:
        raise ValueError('RG01 migration changes more than the opening docstring')
    return {'historical_identity':historical_identity,'observed_identity':descriptor['identity'],
            'migration_sha256':hashlib.sha256((core/'assets/calibration/rg01-header-migration.json').read_bytes()).hexdigest()}
