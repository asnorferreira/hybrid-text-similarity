import argparse
import json
import os
from pathlib import Path

from pymongo import MongoClient

from hts_core.adapters.dataset_mongo import import_version
from hts_core.adapters.dataset_store import canonical, read_jsonl, verify_seal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True)
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    if not args.database.startswith('hts_dataset_s4_check_'):
        raise ValueError('teste deve usar namespace exclusivo identificado')
    try:
        with MongoClient(os.environ['HTS_DATASET_MONGO_URI'], serverSelectionTimeoutMS=10000) as client:
            baseline = {name: {c: client[name][c].count_documents({}) for c in ('documents', 'comparisons', 'reports')}
                        for name in ('hts_s2_development', 'hts_s3_development')}
            database = client[args.database]
            first = import_version(args.dataset, database)
            second = import_version(args.dataset, database)
            assert first == second
            assert database.datasets.count_documents({'_id': first['version']}) == 1
            pair = read_jsonl(Path(args.dataset)/'pairs.jsonl')[0]
            key = first['version'] + ':' + pair['id']
            doc = database.dataset_pairs.find_one({'_id': key})
            database.dataset_pairs.update_one({'_id': key}, {'$set': {'sha256': 'deliberately-corrupt-development-check'}})
            try:
                try:
                    import_version(args.dataset, database)
                except ValueError:
                    conflict = True
                else:
                    conflict = False
            finally:
                database.dataset_pairs.update_one({'_id': key}, {'$set': {'sha256': doc['sha256']}})
            assert conflict
            assert database.datasets.find_one({'_id': first['version']})['state'] == 'integrity_conflict'
            database.dataset_pairs.update_one({'_id': key}, {'$set': {'pair': {**doc['pair'], 'text': doc['pair']['text'] + ' deliberate test corruption'}}})
            try:
                try:
                    import_version(args.dataset, database)
                except ValueError:
                    body_conflict = True
                else:
                    body_conflict = False
                assert body_conflict
                assert database.datasets.find_one({'_id': first['version']})['state'] == 'integrity_conflict'
            finally:
                database.dataset_pairs.update_one({'_id': key}, {'$set': {'pair': doc['pair'], 'sha256': doc['sha256']}})
            final = import_version(args.dataset, database)
            partial_database = client[args.database + '_partial']
            class InterruptingPairs:
                def __init__(self, collection):
                    self.collection = collection
                    self.remaining = 3

                def update_one(self, *args, **kwargs):
                    if not self.remaining:
                        raise OSError('controlled client interruption, not a Mongo server outage')
                    self.remaining -= 1
                    return self.collection.update_one(*args, **kwargs)

                def __getattr__(self, name):
                    return getattr(self.collection, name)

            class PartialDatabase:
                name = partial_database.name
                datasets = partial_database.datasets
                dataset_pairs = InterruptingPairs(partial_database.dataset_pairs)

            if partial_database.dataset_pairs.count_documents({}) or partial_database.datasets.count_documents({}):
                raise ValueError('namespace de interrupção precisa ser novo; preserve a tentativa anterior')
            try:
                import_version(args.dataset, PartialDatabase())
            except OSError:
                pass
            else:
                raise AssertionError('interrupção controlada não ocorreu')
            partial_count = partial_database.dataset_pairs.count_documents({'version': first['version']})
            assert partial_count == 3
            assert partial_database.datasets.find_one({'_id': first['version']})['state'] == 'importing'
            resumed = import_version(args.dataset, partial_database)
            assert resumed['pairs'] == first['pairs']
            after = {name: {c: client[name][c].count_documents({}) for c in ('documents', 'comparisons', 'reports')}
                     for name in baseline}
            assert after == baseline
            print(json.dumps({'first': first, 'second': second, 'conflict_detected': conflict, 'body_conflict_detected': body_conflict,
                              'final': final, 'controlled_client_partial_count': partial_count, 'resumed': resumed,
                              'legacy_counts_before': baseline, 'legacy_counts_after': after,
                              'limitations': 'counts only; no transaction; identified development records retained'}))
    except Exception as exc:
        raise SystemExit('Mongo check failed: ' + type(exc).__name__ + '; details omitted to protect credentials') from None


if __name__ == '__main__':
    main()
