from pathlib import Path

from hts_core.adapters.dataset_store import identity, read_json


RESOURCE_IDENTITY = '86763b23b72b169bb0e6796afc547c61168ed7c4a31aa6ffe16c00dc8a7833ed'


def load_p1_resources(semantic):
    from hts_core.adapters.resources import idf_resource, load_policy
    path = Path(__file__).resolve().parents[3]/'assets/calibration/p1-resources.r2.json'
    frozen = read_json(path)
    if (frozen.get('identity') != RESOURCE_IDENTITY or
        identity({k:v for k,v in frozen.items() if k!='identity'}) != RESOURCE_IDENTITY):
        raise ValueError('P1 frozen RG01 resources changed')
    lexical, descriptor = idf_resource()
    from hts_core.adapters.resource_migrations import verify_idf_header_migration
    original = read_json(path.with_name('p1-resources.json'))
    migration = verify_idf_header_migration(descriptor,original['application_idf_identity'])
    if frozen['parent_identity'] != original['identity'] or frozen['header_migration_sha256'] != migration['migration_sha256']:
        raise ValueError('P1 resource migration differs')
    policy, _ = load_policy()
    if (descriptor['identity'] != frozen['application_idf_identity'] or
        policy['file_sha256'] != frozen['policy_file_sha256'] or semantic.identity != frozen['model_identity']):
        raise ValueError('P1 scoring resources differ from frozen application RG01')
    return lexical, policy, frozen
