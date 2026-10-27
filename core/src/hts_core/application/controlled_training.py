from datetime import datetime, timezone
import hashlib
import importlib.metadata
from pathlib import Path
import random
import time
import platform
import sys

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import annotation_examples, inspect_dataset, save_json_new
from hts_core.adapters.idf_contract import validate_training_idf_contract
from hts_core.adapters.training_contract import SCHEMA, memory_snapshot, readiness, validate_s5b
from hts_core.application.experiment_preparation import code_identity


def training_entry(protocol, reference, dataset, idf, annotations, campaign, task, destination, execute=False, resume=None):
    config=read_json(protocol)
    validate_s5b(config)
    if task not in ('H1','H2'):
        raise ValueError('unknown S5B task')
    reference_config=read_json(reference)
    if identity(reference_config) != config['reference_protocol_identity']:
        raise ValueError('S5A structural reference differs')
    data=inspect_dataset(dataset,reference_config)
    if data['manifest']['version'] != config['dataset_version']:
        raise ValueError('S5B dataset differs')
    idf_report=validate_training_idf_contract(dataset,idf,config['idf_identity'])
    bundle=read_json(annotations)
    if bundle['task'] != task or any(bundle.get(k) != v for k,v in config['annotation'].items()):
        raise ValueError('annotation task/modality/procedure/rubric differs')
    if hashlib.sha256((Path(campaign)/'rubrics.md').read_bytes()).hexdigest() != config['rubric_sha256']:
        raise ValueError('rubric bytes changed')
    plan=read_json(Path(campaign)/'campaign-plan.json')
    selection=read_json(Path(campaign)/'selection-private.json')
    if identity(plan) != config['campaign_plan_identity'] or identity(selection) != config['selection_identity']:
        raise ValueError('pre-annotation campaign plan/selection differs')
    fields=('pair_id','source_id','source_sentence_id','suspect_sentence_id','source_text_sha256','suspect_text_sha256')
    if [tuple(r[k] for k in fields) for r in bundle['records']] != [tuple(r[k] for k in fields) for r in selection]:
        raise ValueError('annotations do not cover exactly the preselected observations')
    examples={}; counts={}
    for split in ('train','validation'):
        examples[split],counts[split]=annotation_examples(bundle,data,reference_config,split)
    if task == 'H2' and (bundle['schema'] != 'hts-annotations-2' or any(r['target'] not in (0,.25,.5,.75,1,None) for r in bundle['records'])):
        raise ValueError('H2 adopted axes and discrete anchors required')
    bindings={'protocol':identity(config),'schema':identity(read_json(SCHEMA)), 'dataset':config['dataset_version'],
              'idf':config['idf_identity'],'annotations':identity(bundle),'rubric':config['rubric_sha256'],
              'campaign_plan':config['campaign_plan_identity'],'selection':config['selection_identity'],
              'code':code_identity(),'seed':config['seed'],'task':task,'base':config['siamese']['base'],
              'revision':config['siamese']['revision'],
              'environment':{k:importlib.metadata.version(k) for k in ('torch','numpy','scipy','scikit-learn','sentence-transformers','safetensors')}}
    from hts_core.adapters.semantic import cache_path, FILES, MODEL, REVISION, digest
    model_descriptor=read_json(cache_path()/'hts-model.json')
    if model_descriptor['model'] != MODEL or model_descriptor['revision'] != REVISION:
        raise ValueError('local model descriptor differs from pinned model')
    for name in FILES:
        if digest(cache_path()/name) != model_descriptor['files'][name]:
            raise ValueError('local model bytes differ: '+name)
    bindings['base_assets']=identity(model_descriptor)
    bindings['environment'].update(python=sys.version,platform=platform.platform())
    out=Path(destination); out.mkdir(parents=True,exist_ok=False)
    report=readiness(config,task,examples,memory_snapshot())
    report.update(bindings=bindings,counts=counts,idf=idf_report,utc=datetime.now(timezone.utc).isoformat(),
                  requested_execution=execute,training_executed=False,final_test_predictions=False)
    save_json_new(out/'readiness.json',report)
    if not execute:
        return report
    if not report['releasable']:
        save_json_new(out/'attempt.json',{'status':'blocked_before_model_load','blockers':report['blockers'],
                                        'bindings':bindings,'training_executed':False})
        raise PermissionError('; '.join(report['blockers']))
    if not readiness(config,task,examples,memory_snapshot())['releasable']:
        raise PermissionError('resources changed before model load')
    claim=Path(campaign)/f'execution-{task}-claim.json'
    if resume is None:
        save_json_new(claim,{'bindings':bindings,'first_destination':str(out.resolve()),'attempts':1})
    elif not claim.exists() or read_json(claim)['bindings'] != bindings:
        raise ValueError('resume requires existing compatible logical attempt')
    if resume is not None:
        from hts_core.adapters.training_runtime import validate_resume_claim
        validate_resume_claim(resume,read_json(claim))
    save_json_new(out/'attempt.json',{'status':'started','bindings':bindings,'utc':datetime.now(timezone.utc).isoformat()})
    try:
        if task == 'H1':
            if resume is not None:
                raise ValueError('H1 single fixed fit has no optimizer resume')
            result=_run_h1(examples,config,bindings,idf,out,data)
        else:
            import numpy as np
            import torch
            from hts_core.adapters.trainable_siamese import load_local_trainable
            from hts_core.adapters.training_runtime import train_loop, load_training_checkpoint
            torch.set_num_threads(config['budget']['threads'])
            random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])
            model,model_identity=load_local_trainable(config)
            save_json_new(out/'base-model.json',model_identity)
            if resume is None:
                _baseline_h2(model,examples,out,config)
            else:
                original=Path(read_json(claim)['first_destination'])/'baseline-metrics.json'
                if not original.is_file():
                    raise ValueError('resume requires preserved original fixed baseline metrics')
                save_json_new(out/'baseline-reference.json',{'path':str(original.resolve()),
                    'sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'bindings':bindings})
            optimizer=torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                lr=config['siamese']['learning_rate'],weight_decay=config['siamese']['weight_decay'])
            result=train_loop(model,optimizer,examples['train'],examples['validation'],config['budget'],bindings,
                              out/'training',config['seed'],resume=resume)
            if result['best_checkpoint'] and Path(result['best_checkpoint']).is_dir():
                selected=load_training_checkpoint(result['best_checkpoint'],model,optimizer,bindings)
                save_json_new(out/'selected-load-verification.json',{'loaded':True,'epoch':selected['epoch'],'bindings':bindings})
            save_json_new(out/'token-windows.json',model.encoder.diagnostics)
        save_json_new(out/'result.json',result)
        return result
    except Exception as exc:
        save_json_new(out/'failure.json',{'type':type(exc).__name__,'message':str(exc),'bindings':bindings})
        raise


def _h1_features(lexical, semantic, learned):
    from hts_core.domain.hybrid import bounded
    l = bounded(lexical)
    s = bounded(semantic,-1,1)
    values: dict[str, float | list[float]] = dict(lexical=l,semantic=s,fixed_fusion=.4*l+.6*max(0,s))
    if learned:values['learned_fusion']=[l,max(0,s)]
    return values


def _run_h1(examples, config, bindings, idf, out, dataset=None):
    import numpy as np
    from hts_core.adapters.semantic import SemanticEncoder
    from hts_core.adapters.nlp import analyze, STOPWORDS
    from hts_core.domain.preprocess import lexical_tokens
    from hts_core.domain.lexical import ReferenceIdf, cosine
    from hts_core.adapters.training_classifiers import fit_classifiers, save_fitted_classifiers
    from hts_core.adapters.training_contract import memory_snapshot
    table=read_json(Path(idf)/'idf.json')
    lexical=ReferenceIdf(table['n_docs'],table['df'],table['version'])
    semantic=SemanticEncoder()
    started=time.monotonic()
    save_json_new(out/'base-model.json',semantic.identity)
    features={}; cache=[]
    for split, rows in examples.items():
        features[split]={system:[] for system in config['h1']['features_by_system']}
        for i,row in enumerate(rows):
            if time.monotonic()-started >= config['budget']['feature_wall_seconds']:
                raise TimeoutError('feature preparation wall limit reached')
            if memory_snapshot()['rss_bytes'] > config['budget']['process_rss_limit_bytes']:
                raise MemoryError('inference RSS cap reached')
            a,b=row['input'].source_text,row['input'].suspect_text
            l=cosine(lexical.vector(lexical_tokens(a,analyze,STOPWORDS)),lexical.vector(lexical_tokens(b,analyze,STOPWORDS)))
            emb,diagnostics=semantic.encode([a,b])
            s=float(np.clip(emb[0]@emb[1],-1,1))
            values=_h1_features(l,s,'learned_fusion' in features[split])
            for system,value in values.items():
                features[split][system].append(value)
            record={'split':split,'row':i,'trace':row['trace'],'features':values,'token_windows':diagnostics,'bindings':bindings}
            save_json_new(out/f'features/{split}-{i:04}.json',record)
            cache.append(record)
    classifiers = fit_classifiers(features['train'],features['validation'],[r['target'] for r in examples['train']],
                                  [r['target'] for r in examples['validation']],config['h1'],bindings)
    artifacts = save_fitted_classifiers(classifiers,out,bindings)
    baselines = {}
    if config['schema'] in ('hts-s5b-3', 'hts-s5b-4'):
        from hts_core.adapters.training_baselines import fit_baselines, save_baselines
        baselines = fit_baselines(examples,features,bindings)
        artifacts.update(save_baselines(baselines,out,bindings))
    save_json_new(out/'selected-load-verification.json',{'loaded':True,'artifacts':artifacts,'bindings':bindings})
    calibration = None
    if config['schema'] in ('hts-s5b-3', 'hts-s5b-4'):
        from hts_core.application.calibration_execution import run_p1
        if dataset is None:raise ValueError('P1 requires the frozen validation dataset')
        calibration = run_p1(dataset,semantic,config,bindings,out/'calibration',started=started)
    return {'status':'complete','training_executed':True,'training_started':True,'training_completed':True,
            'stop_reason':('four_fixed_fits_and_two_baselines_reloaded' if baselines else 'three_fixed_fits_completed_and_exports_reloaded'),'classifiers':classifiers,
            'baselines':baselines,'calibration':calibration,
            'artifacts':artifacts,'train_count':len(examples['train']),'validation_count':len(examples['validation']),
            'selection':config['selection']['h1']}


def _baseline_h2(model, examples, out, config):
    import torch
    from hts_core.domain.experiments import regression_report
    started=time.monotonic()
    model.eval()
    reports={}
    for split, rows in examples.items():
        raw=[]
        with torch.no_grad():
            for i,row in enumerate(rows):
                if (time.monotonic()-started >= config['budget']['feature_wall_seconds'] or
                    memory_snapshot()['rss_bytes'] > config['budget']['process_rss_limit_bytes']):
                    raise RuntimeError('fixed SBERT baseline resource limit')
                u=model.encoder(row['input'].source_text)
                v=model.encoder(row['input'].suspect_text)
                value=float(torch.clamp(u@v,-1,1))
                if not torch.isfinite(torch.tensor(value)):
                    raise FloatingPointError('nonfinite baseline cosine')
                raw.append(value)
                save_json_new(out/f'baseline/{split}-{i:04}.json',{'raw_cosine':value,'trace':row['trace']})
        reports[split]={'raw_cosines':raw,'metrics_affine_diagnostics':regression_report([r['target'] for r in rows],[(v+1)/2 for v in raw]),
                        'spearman_input':'raw_cosine; positive affine transform has identical ranks',
                        'failures':0,'baseline':'same pinned SBERT before any weight updates'}
    save_json_new(out/'baseline-metrics.json',reports)
