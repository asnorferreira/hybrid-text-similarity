import hashlib
import json
import os
from pathlib import Path
import random
import tempfile
import time

import numpy as np
import torch
from safetensors.torch import load_file, save_file

from hts_core.adapters.dataset_store import identity
from hts_core.adapters.training_contract import memory_snapshot
from hts_core.domain.experiments import regression_report, require_split


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False, suffix='.tmp') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(f.name, path)


def rng_state():
    state = np.random.get_state()
    return {'python':random.getstate(), 'numpy':(state[0],torch.tensor(state[1].astype(np.int64)),state[2],state[3],state[4]),
            'torch':torch.get_rng_state()}


def restore_rng(state):
    random.setstate(state['python'])
    n = state['numpy']
    np.random.set_state((n[0],n[1].numpy().astype(np.uint32),n[2],n[3],n[4]))
    torch.set_rng_state(state['torch'])


def validate_resume_claim(path, claim):
    from hts_core.adapters.checkpoint_retention import safe_path
    cp=safe_path(path)
    root=safe_path(Path(claim['first_destination'])/'training')
    manifest=json.loads(safe_path(cp/'manifest.json').read_text(encoding='utf-8'))
    if cp.parent != root or manifest.get('ownership',{}).get('root') != str(root):
        raise ValueError('resume checkpoint differs from claimed logical execution root')
    if manifest.get('bindings') != claim['bindings']:
        raise ValueError('resume checkpoint differs from claimed bindings')


def save_training_checkpoint(path, model, optimizer, state, bindings, ownership=None):
    from hts_core.adapters.checkpoint_retention import safe_path
    started=time.monotonic()
    path = safe_path(path)
    if path.exists():
        raise FileExistsError('checkpoint destination already exists')
    if any(p.grad is not None for p in model.parameters()):
        raise ValueError('checkpoint requires cleared gradients at safe update boundary')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.checkpoint-', dir=path.parent))
    save_file({k:v.detach().cpu().contiguous() for k,v in model.state_dict().items()}, str(temp/'weights.safetensors'))
    torch.save({'optimizer':optimizer.state_dict(), 'rng':rng_state(), 'state':state}, temp/'local-state.pt')
    manifest = {'schema':'hts-training-checkpoint-1', 'bindings':bindings, 'bindings_identity':identity(bindings),
                'files':{n:file_hash(temp/n) for n in ('weights.safetensors','local-state.pt')},
                'safe_boundary':'after_optimizer_step_and_zero_grad; no pending accumulation', 'scheduler':None,
                'serialization':'safetensors weights; own local torch state, weights_only=True on load; hashes are integrity not authentication'}
    manifest['checkpoint_write_seconds']=time.monotonic()-started
    if ownership is not None:
        manifest['ownership']=ownership
    atomic_json(temp/'manifest.json',manifest)
    before_rng=rng_state()
    try:
        load_training_checkpoint(temp,model,optimizer,bindings)
    finally:
        restore_rng(before_rng)
    manifest['checkpoint_write_seconds']=time.monotonic()-started
    atomic_json(temp/'manifest.json',manifest)
    os.replace(temp,path)
    return manifest


def load_training_checkpoint(path, model, optimizer, bindings):
    from hts_core.adapters.checkpoint_retention import safe_path
    path = safe_path(path)
    manifest = json.loads(safe_path(path/'manifest.json').read_text(encoding='utf-8'))
    if (manifest.get('schema') != 'hts-training-checkpoint-1' or manifest.get('bindings') != bindings
            or manifest.get('bindings_identity') != identity(bindings)):
        raise ValueError('checkpoint identity conflict')
    if set(manifest['files']) != {'weights.safetensors','local-state.pt'}:
        raise ValueError('checkpoint components missing or unknown')
    for name, expected in manifest['files'].items():
        safe_path(path/name)
        if file_hash(path/name) != expected:
            raise ValueError('checkpoint bytes altered: '+name)
    model.load_state_dict(load_file(str(path/'weights.safetensors')), strict=True)
    payload = torch.load(path/'local-state.pt', map_location='cpu', weights_only=True)
    if set(payload) != {'optimizer','rng','state'}:
        raise ValueError('invalid local state components')
    optimizer.load_state_dict(payload['optimizer'])
    restore_rng(payload['rng'])
    if 'elapsed_seconds' in payload['state']:
        payload['state']['elapsed_seconds']+=manifest['checkpoint_write_seconds']
    return payload['state']


def validate_rows(rows, split):
    require_split(split)
    if not rows:
        raise ValueError('empty training/validation data')
    for row in rows:
        from hts_core.domain.experiments import ModelInput
        if type(row.get('input')) is not ModelInput or type(row.get('target')) not in (int,float) or not np.isfinite(row['target']) or not 0 <= row['target'] <= 1:
            raise ValueError('training row requires two texts and finite target')
        if row.get('trace',{}).get('split') != split:
            raise PermissionError('row split differs from operation; test closed')


def train_loop(model, optimizer, train, validation, budget, bindings, destination, seed,
               resume=None, clock=time.monotonic, resources=memory_snapshot, pause_after_updates=None):
    validate_rows(train,'train'); validate_rows(validation,'validation')
    expected = {id(p) for p in model.parameters() if p.requires_grad}
    actual = [id(p) for group in optimizer.param_groups for p in group['params']]
    if expected != set(actual) or len(actual) != len(set(actual)):
        raise ValueError('optimizer parameters differ from trainable model parameters')
    from hts_core.adapters.checkpoint_retention import safe_path
    out = safe_path(destination)
    out.mkdir(parents=True, exist_ok=False)
    state = {'epoch':0,'cursor':0,'order':[], 'updates':0,'history':[], 'best_mse':None,'best_checkpoint':None,
             'bad_epochs':0,'elapsed_seconds':0.,'epoch_squared_error':0.,'epoch_samples':0,'status':'running',
             'logical_bindings_identity':identity(bindings),'sampled_peak_rss_bytes':0}
    if resume is not None:
        state = load_training_checkpoint(resume,model,optimizer,bindings)
        if state['status'] not in ('interrupted','running'):
            raise ValueError('terminal budget/patience/completed run cannot extend itself by resume')
        state['status']='running'
    from hts_core.adapters.checkpoint_retention import CheckpointRetention
    retention=CheckpointRetention(out,bindings,resume)
    state['checkpoint_retention']=retention.owner
    state['elapsed_seconds']=max(state['elapsed_seconds'],retention.record.get('logical_elapsed_seconds',0.))
    prior_elapsed = state['elapsed_seconds']
    persisted_best={'checkpoint':state['best_checkpoint'],'mse':state['best_mse']}
    started = clock()
    optimizer.zero_grad(set_to_none=True)

    def elapsed():
        return prior_elapsed+clock()-started

    def stop_reason():
        snapshot = resources()
        state['sampled_peak_rss_bytes'] = max(state['sampled_peak_rss_bytes'],snapshot['rss_bytes'])
        if snapshot['rss_bytes'] > budget['process_rss_limit_bytes']:
            return 'rss_limit'
        if elapsed() >= budget['maximum_wall_seconds']:
            return 'wall_limit'
        if state['updates'] >= budget['maximum_optimizer_updates']:
            return 'optimizer_update_limit'
        return None

    def checkpoint_path():
        return retention.path(state)

    def checkpoint():
        state['elapsed_seconds']=elapsed()
        cp = checkpoint_path()
        if not retention.fits(model,budget['checkpoint_disk_limit_bytes']):
            state['status']='partial'; state['stop_reason']='checkpoint_disk_limit'
            if state['best_checkpoint'] != persisted_best['checkpoint']:
                state['unpersisted_best_candidate']={'checkpoint':state['best_checkpoint'],'mse':state['best_mse']}
                state['best_checkpoint']=persisted_best['checkpoint']; state['best_mse']=persisted_best['mse']
            atomic_json(out/'progress.json',state)
            return None
        retention.publish(cp,model,optimizer,state,budget['checkpoint_disk_limit_bytes'])
        persisted_best.update(checkpoint=state['best_checkpoint'],mse=state['best_mse'])
        state['elapsed_seconds']=elapsed()
        retention.record['logical_elapsed_seconds']=state['elapsed_seconds']
        retention.commit()
        return cp

    try:
        initial_reason=stop_reason()
        if initial_reason:
            state.update(status='partial',stop_reason=initial_reason,elapsed_seconds=elapsed())
            atomic_json(out/'progress.json',state)
            return state
        if resume is None and checkpoint() is None:
            return state
        while state['epoch'] < budget['maximum_epochs']:
            if not state['order']:
                state['order']=list(range(len(train)))
                random.Random(seed+state['epoch']).shuffle(state['order'])
            while state['cursor'] < len(train):
                reason = stop_reason()
                if reason:
                    state.update(status='partial',stop_reason=reason)
                    checkpoint(); return state
                indices = state['order'][state['cursor']:state['cursor']+budget['gradient_accumulation']]
                model.train()
                for i in indices:
                    row=train[i]
                    prediction=model(row['input'].source_text,row['input'].suspect_text)
                    loss=(prediction-prediction.new_tensor(row['target'])).square()
                    if not torch.isfinite(loss):
                        raise FloatingPointError('nonfinite training loss')
                    (loss/len(indices)).backward()
                    state['epoch_squared_error']+=float(loss.detach())
                    state['epoch_samples']+=1
                grads=[p.grad for p in model.parameters() if p.requires_grad and p.grad is not None]
                if not grads or any(not torch.isfinite(g).all() for g in grads):
                    raise FloatingPointError('missing or nonfinite gradients')
                optimizer.step(); optimizer.zero_grad(set_to_none=True)
                if any(not torch.isfinite(p).all() for p in model.parameters()):
                    raise FloatingPointError('nonfinite updated parameters')
                state['updates']+=1; state['cursor']+=len(indices)
                state['elapsed_seconds']=elapsed()
                atomic_json(out/'progress.json',state)
                if pause_after_updates is not None and state['updates'] >= pause_after_updates:
                    state.update(status='interrupted',stop_reason='controlled_pause')
                    checkpoint(); return state
            model.eval()
            predictions=[]
            with torch.no_grad():
                for row in validation:
                    snapshot=resources()
                    if snapshot['rss_bytes'] > budget['process_rss_limit_bytes'] or elapsed() >= budget['maximum_wall_seconds']:
                        state.update(status='partial',stop_reason='validation_resource_limit')
                        checkpoint(); return state
                    predictions.append(float(model(row['input'].source_text,row['input'].suspect_text)))
            if any(not np.isfinite(v) or not 0 <= v <= 1 for v in predictions):
                raise FloatingPointError('invalid validation predictions')
            metrics=regression_report([r['target'] for r in validation],predictions)
            state['epoch']+=1
            state['history'].append({'epoch':state['epoch'],'updates':state['updates'],
                'training_mse':state['epoch_squared_error']/state['epoch_samples'], 'validation':metrics,
                'predictions':predictions, 'elapsed_seconds':elapsed()})
            better=state['best_mse'] is None or metrics['mse'] < state['best_mse']
            state['bad_epochs']=0 if better else state['bad_epochs']+1
            state['cursor']=0; state['order']=[]; state['epoch_squared_error']=0.; state['epoch_samples']=0
            if better:
                state['best_mse']=metrics['mse']
                state['best_checkpoint']=str(checkpoint_path().resolve())
            if state['bad_epochs'] >= budget['early_stopping_patience_epochs']:
                state.update(status='complete',stop_reason='validation_patience')
            elif state['epoch'] >= budget['maximum_epochs']:
                state.update(status='complete',stop_reason='maximum_epochs')
            cp=checkpoint()
            if cp is None or state['status'] != 'running':
                break
        atomic_json(out/'result.json',state)
        return state
    except (Exception,KeyboardInterrupt) as exc:
        atomic_json(out/'failure.json',{'type':type(exc).__name__,'message':str(exc),'elapsed_seconds':elapsed(),
                                      'updates':state['updates'],'policy':'retain earlier safe checkpoints; failed in-memory state not silently resumed'})
        raise
