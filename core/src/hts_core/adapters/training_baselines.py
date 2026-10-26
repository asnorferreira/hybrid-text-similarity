from pathlib import Path

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import save_json_new
from hts_core.domain.experiments import classification_report, ModelInput
from hts_core.domain.hybrid import classify_pair
from hts_core.domain.strings import levenshtein

LABELS=('copia_exata','copia_editada','parafrase','sem_correspondencia_detectada')


def predict_baseline(model, rows, features, expected_bindings=None):
    fields={'schema','system','classes','majority_class','configuration','bindings','identity'}
    if (type(model) is not dict or set(model)!=fields or model['schema']!='hts-h1-baseline-1' or
        model['identity']!=identity({k:v for k,v in model.items() if k!='identity'}) or model['classes']!=list(LABELS)):
        raise ValueError('baseline contract/identity differs')
    if expected_bindings is not None and model['bindings']!=expected_bindings:raise ValueError('baseline bindings differ')
    if model['system']=='baseline_majority':
        if model['majority_class'] not in LABELS:raise ValueError('invalid majority class')
        return [model['majority_class']]*len(rows)
    if model['system']!='baseline_q5v2':raise ValueError('unknown baseline')
    config=read_json(Path(__file__).resolve().parents[3]/'configs/comparison.json')
    keys=('edited_threshold','low_threshold','paraphrase_threshold','lexical_high')
    if model['configuration']!={k:config[k] for k in keys}:raise ValueError('Q5-V2 policy differs')
    if any(len(features[k])!=len(rows) for k in ('lexical','semantic')):raise ValueError('baseline rows differ')
    result=[]
    for row,l,c in zip(rows,features['lexical'],features['semantic'],strict=True):
        value=row['input']
        if type(value) is not ModelInput:raise ValueError('baseline expects only two texts')
        result.append(classify_pair(value.source_text,value.suspect_text,l,max(0,c),
            levenshtein(value.source_text,value.suspect_text),**model['configuration'])['label'])
    return result


def fit_baselines(examples, features, bindings):
    if set(examples)!={'train','validation'} or set(features)!={'train','validation'}:raise PermissionError('test closed')
    labels=[r['target'] for r in examples['train']]
    if set(labels)!=set(LABELS):raise ValueError('all baseline training classes required')
    majority=max(LABELS,key=labels.count)
    config=read_json(Path(__file__).resolve().parents[3]/'configs/comparison.json')
    results={}
    for system in ('baseline_q5v2','baseline_majority'):
        model=dict(schema='hts-h1-baseline-1',system=system,classes=list(LABELS),bindings=bindings,
                   majority_class=majority if system=='baseline_majority' else None,
                   configuration={k:config[k] for k in ('edited_threshold','low_threshold','paraphrase_threshold','lexical_high')} if system=='baseline_q5v2' else {})
        model['identity']=identity(model)
        result={'model':model,'failures':0}
        for split in ('train','validation'):
            predicted=predict_baseline(model,examples[split],features[split],bindings)
            result[split]=classification_report([r['target'] for r in examples[split]],predicted,LABELS)
            result[split+'_predictions']=predicted
        results[system]=result
    return results


def save_baselines(results, destination, bindings):
    artifacts={}
    for system,result in results.items():
        relative=f'classifiers/{system}.json';path=Path(destination)/relative
        save_json_new(path,result['model']);loaded=read_json(path)
        if loaded!=result['model'] or loaded['bindings']!=bindings:raise ValueError('baseline reload differs')
        import hashlib
        artifacts[system]=dict(path=relative,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),identity=loaded['identity'],loaded=True)
    return artifacts
