import copy
import json
import math
from pathlib import Path
import random

import numpy as np
import pytest
import torch
from torch import nn

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.training_contract import validate_s5b, readiness
from hts_core.adapters.trainable_siamese import Siamese, WindowEncoder, pool_tensors
from hts_core.adapters.training_runtime import (train_loop, save_training_checkpoint, load_training_checkpoint,
                                               validate_rows)
from hts_core.adapters.training_classifiers import fit_classifiers, predict_export
from hts_core.domain.experiments import ModelInput

ROOT=Path(__file__).resolve().parents[1]
torch.set_num_threads(2)


def protocol():
    return read_json(ROOT/'configs/experiment_s5b.json')


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding=nn.Embedding(4,3)

    def forward(self,text):
        return torch.nn.functional.normalize(self.embedding(torch.tensor(int(text))),dim=0)


def tiny(dropout=.1):
    return Siamese(TinyEncoder(),dimension=3,hidden=4,dropout=dropout)


def rows(n,split,target=1.):
    return [{'input':ModelInput(str(i%4),str((i+1)%4)),'target':target,'trace':{'split':split}} for i in range(n)]


def resources():
    return {'rss_bytes':10}


def budget():
    result=protocol()['budget']
    result.update(maximum_epochs=2,maximum_optimizer_updates=100,maximum_wall_seconds=1000)
    return result


def seed():
    random.seed(17); np.random.seed(17); torch.manual_seed(17)


def test_adopted_profile_valid():
    assert len(validate_s5b(protocol())) == 64


@pytest.mark.parametrize('key,value',[('seed',True),('seed',9),('allowed_splits',['train','test']),
    ('budget',None),('unknown',1),('status','approved'),('authorization',' '),('adopted_utc','2026-10-25')])
def test_profile_rejects_adulteration(key,value):
    c=protocol(); c[key]=value
    with pytest.raises((ValueError,TypeError)):
        validate_s5b(c)


def test_candidate_cannot_release_training():
    with pytest.raises(ValueError):
        validate_s5b(read_json(ROOT/'configs/experiment_candidates_s5a.json'))


def test_real_readiness_needs_targets_and_memory():
    c=protocol()
    h1={s:[{'target':label} for label in c['h1']['classes'] for _ in range(2)] for s in ('train','validation')}
    low=readiness(c,'H1',h1,{'available_bytes':1024})
    assert low['releasable'] is False and len(low['blockers']) == 1
    assert readiness(c,'H1',h1,{'available_bytes':8*1024**3})['releasable']
    h1['train']=[{'target':'copia_exata'}]*8
    assert len(readiness(c,'H1',h1,{'available_bytes':8*1024**3})['blockers']) == 3
    with pytest.raises(PermissionError):
        readiness(c,'H2',{'test':[]},{'available_bytes':8*1024**3})


def test_h2_constant_targets_do_not_release():
    x={s:[{'target':1.}]*20 for s in ('train','validation')}
    assert len(readiness(protocol(),'H2',x,{'available_bytes':8*1024**3})['blockers']) == 2


def test_symmetry_shared_encoder_gradients_and_eval():
    seed(); model=tiny(); model.eval()
    a=model('0','1'); b=model('1','0')
    assert a.shape == torch.Size([]) and 0 < a.item() < 1
    torch.testing.assert_close(a,b,rtol=0,atol=0)
    a.backward()
    assert model.encoder.embedding.weight.grad is not None
    assert model.encoder.embedding.weight.grad[0].abs().sum() > 0
    assert model.encoder.embedding.weight.grad[1].abs().sum() > 0
    assert list(model._modules) == ['encoder','head']
    assert not model.head[3].training
    model.train(); assert model.head[3].training


def test_frozen_encoder_is_distinct():
    model=Siamese(TinyEncoder(),dimension=3,hidden=4,train_encoder=False)
    model('0','1').backward()
    assert all(p.grad is None and not p.requires_grad for p in model.encoder.parameters())
    assert any(p.grad is not None for p in model.head.parameters())


def test_weighted_pooling_independent_oracle_and_gradients():
    a=torch.tensor([1.,0.],requires_grad=True)
    b=torch.tensor([0.,1.],requires_grad=True)
    result=pool_tensors([a,b],[1,3])
    torch.testing.assert_close(result,torch.tensor([1/math.sqrt(10),3/math.sqrt(10)]))
    result[0].backward()
    assert a.grad is not None and b.grad is not None and b.grad.abs().sum() > 0
    with pytest.raises(ValueError):
        pool_tensors([a],[True])


def test_complete_window_coverage_with_local_tokenizer_only():
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from tokenizers.processors import TemplateProcessing
    from transformers import PreTrainedTokenizerFast
    backend=Tokenizer(WordLevel({'[UNK]':0,'[CLS]':1,'[SEP]':2,'a':3,'b':4},unk_token='[UNK]'))
    backend.pre_tokenizer=Whitespace()
    backend.post_processor=TemplateProcessing(single='[CLS] $A [SEP]',special_tokens=[('[CLS]',1),('[SEP]',2)])
    tokenizer=PreTrainedTokenizerFast(tokenizer_object=backend,unk_token='[UNK]',cls_token='[CLS]',sep_token='[SEP]')
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__(); self.embedding=nn.Embedding(5,3)
        def forward(self,f):
            return {'sentence_embedding':self.embedding(f['input_ids']).mean(1)}
    encoder=WindowEncoder(Encoder(),tokenizer,limit=5)
    value=encoder('a b a b a b a')
    assert encoder.diagnostics[-1] == {'tokens':7,'window_tokens':[3,3,1],'covered':7}
    value[0].backward()
    assert encoder.model.embedding.weight.grad is not None
    assert encoder.model.embedding.weight.grad.abs().sum() > 0


def test_accumulation_last_group_is_not_underweighted(tmp_path):
    class Scalar(nn.Module):
        def __init__(self):
            super().__init__(); self.w=nn.Parameter(torch.tensor(0.))
        def forward(self,a,b):
            return self.w.sigmoid()
    model=Scalar(); optimizer=torch.optim.SGD(model.parameters(),lr=.1)
    b=budget(); b['maximum_epochs']=1
    result=train_loop(model,optimizer,rows(5,'train'),rows(2,'validation'),b,{'case':'artificial'},tmp_path/'run',17,resources=resources)
    first=.025
    s=1/(1+math.exp(-first))
    expected=first-.1*2*(s-1)*s*(1-s)
    assert model.w.item() == pytest.approx(expected,abs=1e-7)
    assert result['updates'] == 2 and result['stop_reason'] == 'maximum_epochs'
    assert result['history'][0]['validation']['spearman']['status'] == 'undefined'


def test_checkpoint_resume_matches_uninterrupted_local_run(tmp_path):
    seed(); full=tiny(); opt=torch.optim.Adam(full.parameters(),lr=.01)
    initial_encoder=full.encoder.embedding.weight.detach().clone()
    a=train_loop(full,opt,rows(5,'train'),rows(3,'validation'),budget(),{'id':'same'},tmp_path/'full',17,resources=resources)
    seed(); partial=tiny(); opt2=torch.optim.Adam(partial.parameters(),lr=.01)
    first=train_loop(partial,opt2,rows(5,'train'),rows(3,'validation'),budget(),{'id':'same'},tmp_path/'part',17,resources=resources,pause_after_updates=1)
    cp=json.loads((tmp_path/'part/latest.json').read_text())['checkpoint']
    resumed=tiny(); opt3=torch.optim.Adam(resumed.parameters(),lr=.01)
    b=train_loop(resumed,opt3,rows(5,'train'),rows(3,'validation'),budget(),{'id':'same'},tmp_path/'resumed',17,resources=resources,resume=cp)
    assert first['status'] == 'interrupted' and a['updates'] == b['updates'] == 4
    assert not torch.equal(initial_encoder,full.encoder.embedding.weight)
    for key, value in full.state_dict().items():
        torch.testing.assert_close(value,resumed.state_dict()[key],rtol=0,atol=0)
    assert [h['validation']['mse'] for h in a['history']] == [h['validation']['mse'] for h in b['history']]


@pytest.mark.parametrize('kind',['tamper','missing','binding','pending_gradient'])
def test_checkpoint_negative_controls(tmp_path,kind):
    model=tiny(); optimizer=torch.optim.Adam(model.parameters())
    if kind == 'pending_gradient':
        model('0','1').backward()
        with pytest.raises(ValueError,match='cleared gradients'):
            save_training_checkpoint(tmp_path/'cp',model,optimizer,{}, {'a':1})
        return
    save_training_checkpoint(tmp_path/'cp',model,optimizer,{}, {'a':1})
    if kind == 'tamper':
        with (tmp_path/'cp/weights.safetensors').open('ab') as f: f.write(b'x')
    elif kind == 'missing':
        m=json.loads((tmp_path/'cp/manifest.json').read_text()); m['files'].pop('local-state.pt')
        (tmp_path/'cp/manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError):
        load_training_checkpoint(tmp_path/'cp',model,optimizer,{'a':2 if kind == 'binding' else 1})


@pytest.mark.parametrize('limit,expected',[('updates','optimizer_update_limit'),('rss','rss_limit'),('clock','wall_limit'),('disk','checkpoint_disk_limit')])
def test_budget_stops_preserve_partial(tmp_path,limit,expected):
    model=tiny(); opt=torch.optim.Adam(model.parameters()); b=budget()
    r=resources; timer=lambda:1.
    if limit == 'updates': b['maximum_optimizer_updates']=1
    elif limit == 'rss': b['process_rss_limit_bytes']=1
    elif limit == 'disk': b['checkpoint_disk_limit_bytes']=1
    else:
        ticks=iter(range(100)); timer=lambda:next(ticks); b['maximum_wall_seconds']=1
    result=train_loop(model,opt,rows(5,'train'),rows(3,'validation'),b,{'artificial':True},tmp_path/'run',17,resources=r,clock=timer)
    assert result['status'] == 'partial' and result['stop_reason'] == expected


def test_patience_and_earliest_tie(tmp_path):
    model=tiny(dropout=0); opt=torch.optim.SGD(model.parameters(),lr=0.)
    b=budget(); b['maximum_epochs']=8
    result=train_loop(model,opt,rows(4,'train'),rows(3,'validation'),b,{},tmp_path/'run',17,resources=resources)
    assert result['stop_reason'] == 'validation_patience' and result['epoch'] == 3
    assert 'epoch-001' in result['best_checkpoint']


def test_test_split_and_mismatched_optimizer_rejected(tmp_path):
    with pytest.raises(PermissionError): validate_rows(rows(2,'test'),'test')
    with pytest.raises(PermissionError): validate_rows(rows(2,'test'),'train')
    with pytest.raises(ValueError): validate_rows(rows(1,'train',float('nan')),'train')
    model=tiny(); other=tiny()
    with pytest.raises(ValueError,match='optimizer'):
        train_loop(model,torch.optim.Adam(other.parameters()),rows(2,'train'),rows(2,'validation'),budget(),{},tmp_path/'no',17)


def test_json_classifiers_portable_without_pickle():
    c=protocol(); labels=c['h1']['classes']
    x=[v for v in (.1,.3,.6,.9) for _ in range(4)]
    y=[v for v in labels for _ in range(4)]
    features={s:x for s in ('lexical','semantic','fixed_fusion')}
    result=fit_classifiers(features,features,y,y,c['h1'],{'case':'artificial'})
    for system,value in result.items():
        assert value['validation']['n'] == 16 and value['failures'] == 0
        assert len(value['model']['coefficients']) == 4
        raw=json.loads(json.dumps(value['model']))
        assert predict_export(raw,x) == value['predictions']
        raw['coefficients'][0][0]+=1
        with pytest.raises(ValueError): predict_export(raw,x)


def test_terminal_budget_cannot_be_extended_by_resume(tmp_path):
    model=tiny(); opt=torch.optim.Adam(model.parameters()); b=budget(); b['maximum_optimizer_updates']=1
    train_loop(model,opt,rows(5,'train'),rows(3,'validation'),b,{},tmp_path/'one',17,resources=resources)
    cp=json.loads((tmp_path/'one/latest.json').read_text())['checkpoint']
    with pytest.raises(ValueError,match='terminal'):
        train_loop(model,opt,rows(5,'train'),rows(3,'validation'),b,{},tmp_path/'two',17,resources=resources,resume=cp)


def test_nonfinite_loss_preserves_failure_without_model(tmp_path):
    class Broken(nn.Module):
        def __init__(self):
            super().__init__(); self.p=nn.Parameter(torch.tensor(1.))
        def forward(self,a,b):
            return self.p*float('nan')
    model=Broken(); opt=torch.optim.Adam(model.parameters())
    with pytest.raises(FloatingPointError):
        train_loop(model,opt,rows(2,'train'),rows(2,'validation'),budget(),{},tmp_path/'failure',17,resources=resources)
    report=json.loads((tmp_path/'failure/failure.json').read_text())
    assert report['updates'] == 0 and report['type'] == 'FloatingPointError'
    assert [p.parent.name for p in (tmp_path/'failure').glob('*/weights.safetensors')] == ['epoch-000-cursor-00000-update-000000-snapshot-0000']


def test_cli_has_no_test_split_or_prediction_operation(capsys):
    from hts_core.cli.training import main
    with pytest.raises(SystemExit) as exc: main(['test'])
    assert exc.value.code == 2
    assert 'invalid choice' in capsys.readouterr().err


def test_missing_checkpoint_weights_rejected_before_deserialization(tmp_path):
    model=tiny(); optimizer=torch.optim.Adam(model.parameters())
    save_training_checkpoint(tmp_path/'cp',model,optimizer,{}, {})
    (tmp_path/'cp/weights.safetensors').rename(tmp_path/'cp/preserved.safetensors')
    with pytest.raises(FileNotFoundError):
        load_training_checkpoint(tmp_path/'cp',model,optimizer,{})


def test_fixed_baseline_uses_same_tiny_encoder_without_updates(tmp_path):
    from hts_core.application.controlled_training import _baseline_h2
    seed(); model=tiny(); before=copy.deepcopy(model.state_dict())
    data={s:rows(3,s) for s in ('train','validation')}
    _baseline_h2(model,data,tmp_path,protocol())
    report=json.loads((tmp_path/'baseline-metrics.json').read_text(encoding='utf-8'))
    with torch.no_grad():
        expected=float(model.encoder('0')@model.encoder('1'))
    assert report['train']['raw_cosines'][0] == pytest.approx(expected)
    assert report['train']['failures'] == 0 and report['validation']['metrics_affine_diagnostics']['n'] == 3
    for key,value in model.state_dict().items():
        torch.testing.assert_close(value,before[key],rtol=0,atol=0)
    assert all(p.grad is None for p in model.parameters())


def test_keyboard_interrupt_keeps_initial_safe_checkpoint(tmp_path):
    class Interrupt(nn.Module):
        def __init__(self):
            super().__init__(); self.p=nn.Parameter(torch.tensor(0.))
        def forward(self,a,b):
            raise KeyboardInterrupt()
    model=Interrupt(); opt=torch.optim.Adam(model.parameters())
    with pytest.raises(KeyboardInterrupt):
        train_loop(model,opt,rows(2,'train'),rows(2,'validation'),budget(),{},tmp_path/'run',17,resources=resources)
    result=json.loads((tmp_path/'run/failure.json').read_text())
    assert result['type'] == 'KeyboardInterrupt' and (tmp_path/'run/latest.json').exists()


def test_disk_limit_does_not_select_unsaved_candidate(tmp_path):
    model=tiny(); opt=torch.optim.Adam(model.parameters()); b=budget()
    b['checkpoint_disk_limit_bytes']=2*1024**2
    calls=0
    def disk_growth():
        nonlocal calls
        calls+=1
        if calls==2:
            (tmp_path/'run/unknown-preserve.bin').write_bytes(b'x'*1024**2)
        return resources()
    result=train_loop(model,opt,rows(4,'train'),rows(3,'validation'),b,{},tmp_path/'run',17,resources=disk_growth)
    assert result['status'] == 'partial' and result['stop_reason'] == 'checkpoint_disk_limit'
    assert result['best_checkpoint'] is None and result['best_mse'] is None
    assert result['unpersisted_best_candidate']['mse'] >= 0
    assert (tmp_path/'run/latest.json').exists()
