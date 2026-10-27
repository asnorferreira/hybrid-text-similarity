import argparse
import json

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.experiment_io import import_annotations, inspect_dataset
from hts_core.application.experiment_preparation import fixture_smoke, prepare


def main(argv=None):
    parser = argparse.ArgumentParser(prog='hts experiment', description='Preparação S5A e avaliação S5C com referência/autorização verificadas')
    sub = parser.add_subparsers(dest='operation', required=True)
    freeze = sub.add_parser('freeze-reference', help='Verifica respostas e congela referência; sem predições')
    for name in ('root', 'campaign', 'imported', 'plan', 'out'):
        freeze.add_argument('--' + name, required=True)
    evaluation = sub.add_parser('evaluate', help='Avaliação final única com referência e autorização vinculadas')
    for name in ('root', 'reference', 'authorization', 'authorization-sha256', 'out'):
        evaluation.add_argument('--' + name, required=True)
    for name in ('preflight', 'fixture', 'import-annotations', 'audit-annotations'):
        command = sub.add_parser(name)
        command.add_argument('--protocol', required=True)
        command.add_argument('--out', required=True)
        if name != 'fixture':
            command.add_argument('--dataset', required=True)
        if name == 'preflight':
            command.add_argument('--idf', required=True)
            command.add_argument('--candidates')
        if name in ('import-annotations', 'audit-annotations'):
            command.add_argument('--annotations', required=True)
            command.add_argument('--split', choices=('train', 'validation', 'test') if name == 'audit-annotations' else ('train', 'validation'), required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == 'freeze-reference':
            from hts_core.application.final_evaluation import freeze_reference
            result = freeze_reference(args.root, args.campaign, args.imported, args.plan, args.out)
            summary = {k: result[k] for k in ('identity', 'eligibility', 'reference_frozen', 'predictions')}
        elif args.operation == 'evaluate':
            from hts_core.application.final_evaluation import evaluate
            summary = evaluate(args.reference, args.authorization, args.authorization_sha256, args.root, args.out)
        elif args.operation == 'preflight':
            result = prepare(args.protocol, args.dataset, args.idf, args.out, args.candidates)
            summary = {k: result[k] for k in ('dataset_version', 'tasks', 'prediction_executed')}
        elif args.operation == 'fixture':
            result = fixture_smoke(args.protocol, args.out)
            summary = {k: result[k] for k in ('scope', 'weights_created')}
        else:
            config = read_json(args.protocol)
            data = inspect_dataset(args.dataset, config)
            summary = import_annotations(args.annotations, args.out, data, config, args.split,
                                         audit_only=args.operation == 'audit-annotations')
        status = 'final_reference_frozen_no_predictions' if args.operation == 'freeze-reference' else 'preparation_complete_not_experiment_release'
        print(json.dumps({'operation': args.operation, 'status': status, **summary}, ensure_ascii=False))
    except (OSError, ValueError, PermissionError, KeyError, TypeError) as exc:
        parser.exit(2, f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
