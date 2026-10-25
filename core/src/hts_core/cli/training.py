import argparse
import json

from hts_core.application.controlled_training import training_entry


def main(argv=None):
    parser=argparse.ArgumentParser(prog='hts training',description='S5B exploratory train/validation only; no test operation')
    parser.add_argument('operation',choices=('readiness','run'))
    for key in ('protocol','reference','dataset','idf','annotations','campaign','out'):
        parser.add_argument('--'+key,required=True)
    parser.add_argument('--task',choices=('H1','H2'),required=True)
    parser.add_argument('--resume')
    args=parser.parse_args(argv)
    try:
        result=training_entry(args.protocol,args.reference,args.dataset,args.idf,args.annotations,args.campaign,
                              args.task,args.out,execute=args.operation=='run',resume=args.resume)
        print(json.dumps({'status':result.get('status','readiness_checked'),'task':args.task,
                          'releasable':result.get('releasable'),'blockers':result.get('blockers',[])},ensure_ascii=False))
    except (OSError,ValueError,PermissionError,RuntimeError,KeyError,TypeError) as exc:
        parser.exit(2,f'{type(exc).__name__}: {exc}\n')


if __name__ == '__main__':
    main()
