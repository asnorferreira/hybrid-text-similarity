import hashlib
from typing import Any

from hts_core.adapters.dataset_store import identity
from hts_core.domain.calibration import calibration_metrics, fit_platt, probabilities
from hts_core.domain.experiments import require_split
from hts_core.domain.experiments import ModelInput


def derivation_examples(dataset, split):
    require_split(split)
    if split != 'validation':raise PermissionError('P1 labels use validation only')
    sources = {s['id']:s for s in dataset['sources']}
    selected = {}; parent = {}; combinations = 0
    def find(group):
        parent.setdefault(group,group)
        while parent[group] != group:group=parent[group]
        return group
    for pair in dataset['pairs']:
        if pair['split'] != split:continue
        group = dataset['components'][pair['id']]
        for source_id in sorted(set(pair['source_ids'])):
            source = sources[source_id]
            if source['split'] != split:raise PermissionError('ancestry crosses split')
            for a in source['sentences']:
                for b in pair['sentences']:
                    combinations += 1
                    target = int(any(p['source_id']==source_id and p['sentence_id']==a['id'] for p in b['ancestors']))
                    key = identity([a['semantic'],b['semantic']])
                    if key not in selected:
                        selected[key] = dict(input=ModelInput(a['semantic'],b['semantic']),targets=set(),groups=set())
                    row = selected[key];row['targets'].add(target);row['groups'].add(group)
                    root = min(find(g) for g in row['groups'])
                    for g in row['groups']:parent[find(g)]=root
    rows = []; conflicts = 0
    for key,row in sorted(selected.items()):
        if len(row['targets']) != 1:
            conflicts += 1
            continue
        rows.append(dict(id=key,input=row['input'],target=next(iter(row['targets'])),
                         component=find(next(iter(row['groups'])))))
    return rows,dict(raw_combinations=combinations,unique_text_pairs=len(selected),
                     conflicting_text_pairs_excluded=conflicts,eligible=len(rows),
                     components=len({r['component'] for r in rows}),formats_are_observations=False,
                     label_origin='S4 recorded sentence ancestry; synthetic derivation, not independent semantic labels')


def export_platt(parameters, bindings):
    if type(bindings) is not dict or not bindings:
        raise ValueError('calibration bindings required')
    value = dict(schema='hts-platt-1',variant='P1',parameters=parameters,bindings=bindings,
                 feature='fixed_fusion',target='sentence_pair_derivation',fit_split='validation',index_unchanged=True)
    value['identity'] = identity(value)
    return value


def predict_platt(value, scores, expected_bindings=None):
    fields = {'schema','variant','parameters','bindings','feature','target','fit_split','index_unchanged','identity'}
    if type(value) is not dict or set(value) != fields or value['identity'] != identity({k:v for k,v in value.items() if k!='identity'}):
        raise ValueError('calibration identity or fields differ')
    if (value['schema'],value['variant'],value['feature'],value['target'],value['fit_split'],value['index_unchanged']) != (
        'hts-platt-1','P1','fixed_fusion','sentence_pair_derivation','validation',True):
        raise ValueError('calibration contract differs')
    if expected_bindings is not None and value['bindings'] != expected_bindings:
        raise ValueError('calibration bindings differ')
    return probabilities(value['parameters']['A'],value['parameters']['B'],scores)


def grouped_evaluation(rows, seed=20261025, folds=3) -> dict[str, Any]:
    groups = sorted({r['component'] for r in rows}, key=lambda g: hashlib.sha256(f'{seed}:{g}'.encode()).hexdigest())
    if len(groups) < 2:
        return dict(status='unavailable',reason='fewer than two independent dependency components',metrics=None,predictions=None,components=len(groups))
    count = min(folds,len(groups))
    assignment = {group:i%count for i,group in enumerate(groups)}
    predicted = [None]*len(rows); audits = []
    for fold in range(count):
        train = [i for i,r in enumerate(rows) if assignment[r['component']] != fold]
        held = [i for i,r in enumerate(rows) if assignment[r['component']] == fold]
        if {rows[i]['target'] for i in train} != {0,1}:
            return dict(status='unavailable',reason='grouped fold fit lacks a target class',metrics=None,predictions=None,components=len(groups))
        params = fit_platt([rows[i]['score'] for i in train],[rows[i]['target'] for i in train])
        values = probabilities(params['A'],params['B'],[rows[i]['score'] for i in held])
        for i,value in zip(held,values,strict=True):predicted[i]=value
        audits.append(dict(fold=fold,fit_ids=[rows[i]['id'] for i in train],evaluation_ids=[rows[i]['id'] for i in held],
            fit_groups=sorted({rows[i]['component'] for i in train}),evaluation_groups=sorted({rows[i]['component'] for i in held})))
    return dict(status='evaluated_out_of_fold',metrics=calibration_metrics([r['target'] for r in rows],predicted),
                raw_metrics=calibration_metrics([r['target'] for r in rows],[r['score'] for r in rows]),
                predictions=predicted,folds=audits,components=len(groups),scope='finite_synthetic_validation; not independent human semantic reference')


def fit_calibration(rows, split, bindings) -> dict[str, Any]:
    require_split(split)
    if split != 'validation':raise PermissionError('P1 fits validation only')
    fields = {'id','score','target','component'}
    if not rows or any(type(r) is not dict or set(r) != fields or not r['id'] or not r['component'] for r in rows):
        raise ValueError('calibration accepts one score and separate labels/groups only')
    if len({r['id'] for r in rows}) != len(rows):raise ValueError('duplicate calibration observation')
    evaluation = grouped_evaluation(rows)
    params = fit_platt([r['score'] for r in rows],[r['target'] for r in rows])
    model = export_platt(params,bindings)
    predicted = predict_platt(model,[r['score'] for r in rows],bindings)
    return dict(model=model,evaluation=evaluation,
        fit_diagnostics=dict(scope='resubstitution_diagnostic_not_independent',
            calibrated=calibration_metrics([r['target'] for r in rows],predicted),
            raw=calibration_metrics([r['target'] for r in rows],[r['score'] for r in rows])),
        eligible_ids=[r['id'] for r in rows],fit_split='validation',test_used=False)
