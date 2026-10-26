"""Prepare blank reference inputs only after separate S5C authorization."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import inspect_dataset, save_json_new


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def select(data, plan):
    sources = {s['id']:s for s in data['sources']}
    pairs = [p for p in data['pairs'] if p['split']=='test']
    cells = defaultdict(list)
    for p in pairs:
        if sources[p['source_id']]['split'] != 'test':
            raise ValueError('source split differs from final-reference pair')
        cells[(p['method'],str(p['severity']))].append(p)
    selected,seen = [],set()

    def take(candidates, cross=False):
        for p in sorted(candidates,key=lambda p:sha(str(plan['seed'])+':'+p['id'])):
            src=sources[p['source_id']]
            for b in sorted(p['sentences'],key=lambda b:sha(str(plan['seed'])+':'+p['id']+':'+b['id'])):
                ancestors={a['sentence_id'] for a in b['ancestors'] if a['source_id']==src['id']}
                for a in sorted(src['sentences'],key=lambda a:(a['id'] not in ancestors,sha(a['id']))):
                    if cross and a['id'] in ancestors:
                        continue
                    hashes=(sha(a['semantic']),sha(b['semantic']))
                    if hashes in seen:
                        continue
                    seen.add(hashes)
                    selected.append({'observation_id':f'T{len(selected)+1:03}',
                        'pair_id':p['id'],'source_id':src['id'],'source_sentence_id':a['id'],
                        'suspect_sentence_id':b['id'],'source_text_sha256':hashes[0],
                        'suspect_text_sha256':hashes[1],'source_text':a['semantic'],'suspect_text':b['semantic'],
                        'split':'test','stratum':'nonancestral_cross' if cross else str((p['method'],p['severity']))})
                    return
        raise ValueError('planned coverage cannot be filled without duplicates; preserve plan, do not replace after labels')

    if len(cells)+plan['extra_nonancestral'] > plan['maximum_observations']:
        raise ValueError('coverage exceeds predeclared campaign ceiling')
    for key in sorted(cells):
        take(cells[key])
    for _ in range(plan['extra_nonancestral']):
        take(pairs,True)
    return selected


def validate_plan(plan):
    expected={'schema','dataset_version','s5b_protocol_identity','rubric_sha256','seed',
              'maximum_observations','batch_size','extra_nonancestral','selection','modality',
              'generator_relationship','status','test_predictions_authorized'}
    if type(plan) is not dict or set(plan)!=expected:
        raise ValueError('reference plan requires exact fields')
    for field in ('dataset_version','s5b_protocol_identity','rubric_sha256'):
        value=plan[field]
        if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('reference identity invalid: '+field)
    for k,v in {'schema':'hts-s5c-reference-plan-1','seed':20261025,'maximum_observations':24,
                'batch_size':8,'extra_nonancestral':4,'selection':'one_per_method_severity_cell_plus_four_nonancestral',
                'modality':'automated_weak','generator_relationship':'shared',
                'status':'prepared_not_authorized','test_predictions_authorized':False}.items():
        if type(plan[k]) is not type(v) or plan[k]!=v:
            raise ValueError('unsupported reference plan field: '+k)
    return identity(plan)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True)
    parser.add_argument('--protocol',default='configs/experiment_s5b.json')
    parser.add_argument('--reference',default='configs/experiment_s5a.json')
    parser.add_argument('--rubric',default='artifacts/s5b-01/rubrics.md')
    parser.add_argument('--check-plan-only',action='store_true')
    parser.add_argument('--authorization-record')
    parser.add_argument('--dataset')
    parser.add_argument('--out')
    args=parser.parse_args(argv)
    plan=read_json(args.plan); plan_id=validate_plan(plan)
    protocol=read_json(args.protocol)
    from hts_core.adapters.training_contract import validate_s5b
    if validate_s5b(protocol)!=plan['s5b_protocol_identity'] or protocol['dataset_version']!=plan['dataset_version']:
        parser.error('S5B protocol/dataset identity differs from reference plan')
    if hashlib.sha256(Path(args.rubric).read_bytes()).hexdigest()!=plan['rubric_sha256']:
        parser.error('reference rubric bytes differ')
    if args.check_plan_only:
        print(json.dumps({'plan_identity':plan_id,'status':'plan_checked_no_dataset_opened','labels_produced':0,'predictions':False}))
        return
    if not args.authorization_record or not args.dataset or not args.out:
        parser.error('preparation requires separate authorization record, dataset and new output')
    authorization=read_json(args.authorization_record)
    if (set(authorization)!= {'action','plan_identity','user_instruction_ref','predictions_authorized'} or
            authorization['action']!='prepare_final_reference_inputs' or authorization['plan_identity']!=plan_id or
            type(authorization['user_instruction_ref']) is not str or not authorization['user_instruction_ref'].strip() or
            authorization['predictions_authorized'] is not False):
        parser.error('authorization must reference actual separate user instruction; no prediction authorization')
    data=inspect_dataset(args.dataset,read_json(args.reference))
    if data['manifest']['version']!=plan['dataset_version']:
        parser.error('final reference dataset differs')
    observations=select(data,plan)
    out=Path(args.out); out.mkdir(parents=True,exist_ok=False)
    save_json_new(out/'selection-private.json',observations)
    prompt='Apply the preserved H1/H2 rubric to the two supplied sentences. Do not infer labels from construction. Report factual reasoning and quotes; insufficient context or unresolved ambiguity has null target. Modality automated_weak/shared; no human or independent review. Do not use system scores. Return observation_id, H1 status/target/reason/quote and H2 axes/status/target/reason/quote.'
    for index,start in enumerate(range(0,len(observations),plan['batch_size']),1):
        rows=[{k:r[k] for k in ('observation_id','source_text','suspect_text')} for r in observations[start:start+plan['batch_size']]]
        save_json_new(out/f'batch-{index:02}-input.json',{'prompt':prompt,'rubric':Path(args.rubric).read_text(encoding='utf-8'),'observations':rows})
    save_json_new(out/'preparation-receipt.json',{'utc':datetime.now(timezone.utc).isoformat(),
        'plan_identity':plan_id,'authorization_record_identity':identity(authorization),
        'selection_identity':identity(observations),'selected':len(observations),'labels_produced':0,
        'test_texts_exposed_for_annotation':True,'predictions':False,'reference_frozen':False,
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')}})
    print(json.dumps({'status':'blank_inputs_prepared_not_reference_labels','selected':len(observations),'predictions':False}))


if __name__=='__main__':
    main()
