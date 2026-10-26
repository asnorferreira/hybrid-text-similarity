import copy
import hashlib
import json

import pytest

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.resource_migrations import verify_idf_header_migration
from hts_core.adapters.resources import idf_resource
from pathlib import Path


@pytest.mark.parametrize('change',['table','pipeline','source'])
def test_header_migration_rejects_other_resource_changes(change,monkeypatch):
    _,descriptor = idf_resource()
    frozen = read_json(Path(__file__).resolve().parents[1]/'assets/calibration/p1-resources.json')
    assert verify_idf_header_migration(descriptor,frozen['application_idf_identity'])
    value = copy.deepcopy(descriptor)
    if change == 'source':
        from hts_core.adapters import resource_migrations
        original = resource_migrations.read_json
        def changed(path):
            result = original(path)
            result['removed_prefix'] += 'x'
            return result
        monkeypatch.setattr(resource_migrations,'read_json',changed)
    elif change == 'table':value['table_sha256'] = '0'*64
    else:value['observed_pipeline']['src/hts_core/domain/text.py'] = '0'*64
    if change != 'source':
        value['identity'] = hashlib.sha256(json.dumps({k:v for k,v in value.items() if k!='identity'},sort_keys=True).encode()).hexdigest()
    with pytest.raises(ValueError):verify_idf_header_migration(value,frozen['application_idf_identity'])
