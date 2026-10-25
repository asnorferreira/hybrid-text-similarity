import argparse
import json
import os
from pathlib import Path

from hts_core.adapters.dataset_store import export_bundle, import_bundle, read_json, verify_seal


def main(argv=None):
    parser = argparse.ArgumentParser(prog='hts dataset')
    sub = parser.add_subparsers(dest='action', required=True)
    collect = sub.add_parser('coletar')
    collect.add_argument('--plan', required=True)
    collect.add_argument('--out', required=True)
    for name in ('piloto', 'gerar'):
        command = sub.add_parser(name)
        command.add_argument('--config', required=True)
        command.add_argument('--corpus', required=True)
        command.add_argument('--out', required=True)
    candidates = sub.add_parser('incorporar-cache')
    candidates.add_argument('--dataset', required=True)
    candidates.add_argument('--records', nargs='+', required=True)
    candidates.add_argument('--out', required=True)
    for name in ('validar', 'verificar-hashes'):
        command = sub.add_parser(name)
        command.add_argument('--dataset', required=True)
    idf_validation = sub.add_parser('validar-idf')
    idf_validation.add_argument('--dataset', required=True)
    idf_validation.add_argument('--idf', required=True)
    for name in ('formatos', 'revisao', 'idf-treino', 'exportar'):
        command = sub.add_parser(name)
        command.add_argument('--dataset', required=True)
        command.add_argument('--out', required=True)
        if name == 'formatos':
            command.add_argument('--limit', type=int)
        if name == 'revisao':
            command.add_argument('--seed', type=int, required=True)
            command.add_argument('--percent', type=int, default=20)
            command.add_argument('--pilot-count', type=int)
    imported = sub.add_parser('importar')
    imported.add_argument('--bundle', required=True)
    imported.add_argument('--out', required=True)
    review = sub.add_parser('importar-revisao')
    review.add_argument('--package', required=True)
    review.add_argument('--responses', required=True)
    review.add_argument('--out', required=True)
    freeze = sub.add_parser('congelar')
    freeze.add_argument('--dataset', required=True)
    freeze.add_argument('--review', required=True)
    freeze.add_argument('--authorization', required=True)
    freeze.add_argument('--out', required=True)
    mongo = sub.add_parser('importar-mongo')
    mongo.add_argument('--dataset', required=True)
    mongo.add_argument('--database', required=True)
    llm = sub.add_parser('llm-candidato')
    llm.add_argument('--request', required=True)
    llm.add_argument('--limits', required=True)
    llm.add_argument('--cache', required=True)
    args = parser.parse_args(argv)
    if args.action == 'coletar':
        from hts_core.adapters.dataset_collect import collect_fixed
        result = collect_fixed(read_json(args.plan), args.out)
    elif args.action in {'piloto', 'gerar'}:
        from hts_core.application.dataset_pipeline import build_local
        config = read_json(args.config)
        if args.action == 'gerar' and config['purpose'] != 'experimental_candidate':
            raise ValueError('gerar exige configuração experimental aprovada; use piloto para desenvolvimento')
        result = build_local(config, args.corpus, args.out)
    elif args.action == 'incorporar-cache':
        from hts_core.application.dataset_pipeline import add_cached_candidates
        result = add_cached_candidates(args.dataset, [read_json(p) for p in args.records], args.out)
    elif args.action == 'validar':
        from hts_core.adapters.dataset_validation import validate_data
        result = validate_data(args.dataset)
    elif args.action == 'verificar-hashes':
        result = verify_seal(args.dataset)
    elif args.action == 'validar-idf':
        from hts_core.adapters.dataset_validation import validate_training_idf
        result = validate_training_idf(args.dataset, args.idf)
    elif args.action == 'formatos':
        from hts_core.adapters.dataset_formats import add_formats
        result = add_formats(args.dataset, args.out, args.limit)
    elif args.action == 'idf-treino':
        from hts_core.application.dataset_pipeline import build_training_idf
        result = build_training_idf(args.dataset, args.out)
    elif args.action == 'revisao':
        from hts_core.adapters.dataset_review import prepare_review
        result = prepare_review(args.dataset, args.out, args.seed, args.percent, args.pilot_count)
    elif args.action == 'importar-revisao':
        from hts_core.adapters.dataset_review import import_review
        result = import_review(args.package, args.responses, args.out)
    elif args.action == 'congelar':
        from hts_core.adapters.dataset_review import freeze
        result = freeze(args.dataset, args.review, read_json(args.authorization), args.out)
    elif args.action == 'exportar':
        result = {'version': export_bundle(args.dataset, args.out)}
    elif args.action == 'importar':
        result = import_bundle(args.bundle, args.out)
    elif args.action == 'llm-candidato':
        from hts_core.adapters.dataset_llm import generate_candidate
        result = generate_candidate(read_json(args.request), args.cache, read_json(args.limits))
        result = {k: result[k] for k in ('request_id', 'cache_key', 'status')}
    else:
        from pymongo import MongoClient
        from hts_core.adapters.dataset_mongo import import_version
        uri = os.environ.get('HTS_DATASET_MONGO_URI')
        if not uri:
            raise ValueError('defina HTS_DATASET_MONGO_URI sem imprimir seu conteúdo')
        try:
            with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
                result = import_version(args.dataset, client[args.database])
        except Exception as exc:
            raise SystemExit('Falha na importação Mongo: ' + type(exc).__name__ + '; detalhes omitidos para proteger credenciais') from None
    if isinstance(result, dict) and 'files' in result and 'version' in result:
        result = {k: result[k] for k in ('version', 'metadata')}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
