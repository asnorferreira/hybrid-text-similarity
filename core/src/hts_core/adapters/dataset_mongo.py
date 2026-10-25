from pathlib import Path

from hts_core.adapters.dataset_store import canonical, digest, read_jsonl, verify_seal
from hts_core.adapters.dataset_validation import validate_data


def import_version(folder, database):
    if not database.name.startswith('hts_dataset_'):
        raise PermissionError('namespace exclusivo hts_dataset_ obrigatório; não usar banco de usuários')
    manifest = verify_seal(folder)
    validate_data(folder)
    version = manifest['version']
    dataset = {'_id': version, 'manifest': manifest, 'manifest_sha256': digest(canonical(manifest)), 'state': 'importing'}
    previous = database.datasets.find_one({'_id': version})
    if previous and previous['manifest_sha256'] != dataset['manifest_sha256']:
        raise ValueError('conflito de versão; não sobrescrever')
    database.datasets.update_one({'_id': version}, {'$setOnInsert': dataset}, upsert=True)
    for pair in read_jsonl(Path(folder)/'pairs.jsonl'):
        key = version + ':' + pair['id']
        body = {'_id': key, 'version': version, 'pair': pair, 'sha256': digest(canonical(pair))}
        previous = database.dataset_pairs.find_one({'_id': key})
        if previous and previous['sha256'] != body['sha256']:
            raise ValueError('conflito de par; não sobrescrever')
        database.dataset_pairs.update_one({'_id': key}, {'$setOnInsert': body}, upsert=True)
    database.datasets.update_one({'_id': version, 'manifest_sha256': dataset['manifest_sha256']}, {'$set': {'state': 'complete'}})
    return {'version': version, 'pairs': database.dataset_pairs.count_documents({'version': version}),
            'status': 'complete', 'atomic': False}
