import argparse
import json

from hts_core.application.human_reference import audit_human_results


def main(argv=None):
    parser = argparse.ArgumentParser(description='Auditar duas respostas humanas cegas, sem predição ou congelamento final.')
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--answers', nargs=2, required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    result = audit_human_results(args.campaign, args.answers, args.out)
    print(json.dumps({'status': result['status'], 'assessors': result['assessors'],
                      'reference_frozen': False, 'predictions': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
