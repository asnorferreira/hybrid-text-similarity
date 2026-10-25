import argparse
import json
from pathlib import Path

from hts_core.adapters.dataset_formats import add_formats
from hts_core.adapters.dataset_operational import build_operational, coverage
from hts_core.adapters.dataset_store import read_json, write_json
from hts_core.application.dataset_pipeline import add_cached_candidates, build_training_idf
from prepare_dataset_sources import prepare


def main():
    parser = argparse.ArgumentParser(description='Reconstrução offline por raw/cache fixados; sem nova geração LLM ou experimentos.')
    parser.add_argument('--collection', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--cache', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--exclusions')
    parser.add_argument('--idf', action='store_true')
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    completed, step = {}, 'sources'
    try:
        config = read_json(args.config)
        prepare(args.collection, args.plan, out/'sources', dict(config))
        completed[step] = read_json(out/'sources/manifest.json')['version']
        step = 'base'
        completed[step] = build_operational(out/'sources', args.collection, config, out/'base')['version']
        step = 'cached'
        records = []
        for path in sorted(Path(args.cache).glob('*.json')):
            body = read_json(path)
            if 'request_id' in body:
                records.append(body)
        if not records:
            raise ValueError('cache real preservado ausente')
        result = add_cached_candidates(out/'base', records, out/'cached', read_json(args.exclusions) if args.exclusions else None)
        completed[step] = result['version']
        if result['metadata']['cache_rejections']:
            raise ValueError('incorporação parcial; cache e rejeições preservados')
        step = 'formatted'
        completed[step] = add_formats(out/'cached', out/'formatted')['version']
        if args.idf:
            step = 'idf'
            completed[step] = build_training_idf(out/'formatted', out/'idf')['version']
        result = {'status': 'reconstructed_from_preserved_raw_cache', 'versions': completed, 'coverage': coverage(out/'formatted'),
                  'LLM_regenerated': False, 'predictive_evaluation': False, 'semantic_training_ready': False}
        write_json(out/'construction.json', result)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        write_json(out/'construction-failure.json', {'failed_step': step, 'completed': completed, 'error_type': type(exc).__name__})
        raise


if __name__ == '__main__':
    main()
