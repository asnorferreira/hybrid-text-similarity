import argparse
import json

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.experiment_io import import_annotations, inspect_dataset
from hts_core.application.experiment_preparation import fixture_smoke, prepare


def main(argv=None):
    parser = argparse.ArgumentParser(prog='hts experiment', description='Preparação S5A; não treina nem abre o teste')
    sub = parser.add_subparsers(dest='operation', required=True)
    for name in ('preflight', 'fixture', 'import-annotations'):
        command = sub.add_parser(name)
        command.add_argument('--protocol', required=True)
        command.add_argument('--out', required=True)
        if name != 'fixture':
            command.add_argument('--dataset', required=True)
        if name == 'preflight':
            command.add_argument('--idf', required=True)
        if name == 'import-annotations':
            command.add_argument('--annotations', required=True)
            command.add_argument('--split', choices=('train', 'validation'), required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == 'preflight':
            result = prepare(args.protocol, args.dataset, args.idf, args.out)
            summary = {k: result[k] for k in ('dataset_version', 'tasks', 'prediction_executed')}
        elif args.operation == 'fixture':
            result = fixture_smoke(args.protocol, args.out)
            summary = {k: result[k] for k in ('scope', 'weights_created')}
        else:
            config = read_json(args.protocol)
            data = inspect_dataset(args.dataset, config)
            summary = import_annotations(args.annotations, args.out, data, config, args.split)
        print(json.dumps({'operation': args.operation, 'status': 'preparation_complete_not_experiment_release', **summary}, ensure_ascii=False))
    except (OSError, ValueError, PermissionError, KeyError, TypeError) as exc:
        parser.exit(2, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
