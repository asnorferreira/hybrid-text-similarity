import json
from pathlib import Path
import shutil
import random

import pytest
import torch
from torch import nn

from hts_core.adapters.checkpoint_retention import CheckpointRetention, tree_bytes
from hts_core.adapters import training_runtime as runtime
from hts_core.adapters.trainable_siamese import Siamese
from hts_core.domain.experiments import ModelInput


def tiny(dropout=.1):
    class Encoder(nn.Module):
        def __init__(self):
            super().__init__(); self.embedding=nn.Embedding(4,3)
        def forward(self,text):
            return torch.nn.functional.normalize(self.embedding(torch.tensor(int(text))),dim=0)
    return Siamese(Encoder(),dimension=3,hidden=4,dropout=dropout)


def rows(n,split):
    return [{'input':ModelInput(str(i%4),str((i+1)%4)),'target':1.,'trace':{'split':split}} for i in range(n)]


def budget():
    result=read(Path(__file__).resolve().parents[1]/'configs/experiment_s5b.json')['budget']
    result.update(maximum_epochs=2,maximum_optimizer_updates=100,maximum_wall_seconds=1000)
    return result


def resources(): return {'rss_bytes':10}


def seed():
    random.seed(17); torch.manual_seed(17)


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def manager(tmp_path):
    root=tmp_path/'run'; root.mkdir()
    model=tiny(0); opt=torch.optim.Adam(model.parameters(),lr=.01)
    return CheckpointRetention(root,{'fixture':'owned'}),model,opt


def publish(m, model, opt, epoch, selected=None):
    state={'epoch':epoch,'cursor':0,'updates':epoch,'best_checkpoint':selected,'status':'running'}
    cp=m.path(state)
    if selected=='self': state['best_checkpoint']=str(cp)
    assert m.fits(model,2*1024**2)
    m.publish(cp,model,opt,state,2*1024**2)
    return cp


def test_retains_latest_and_selected_with_loadable_states(tmp_path):
    m,model,opt=manager(tmp_path)
    initial=publish(m,model,opt,0)
    first=publish(m,model,opt,1,'self')
    assert not initial.exists()
    for epoch in range(2,8):
        last=publish(m,model,opt,epoch,str(first))
        assert {p.name for p in m.root.iterdir() if p.is_dir()}=={first.name,last.name}
        for p in (first,last):
            s=runtime.load_training_checkpoint(p,model,opt,m.bindings)
            assert s['epoch'] in (1,epoch)
        assert Path(read(m.root/'latest.json')['checkpoint']).is_dir()
    improved=publish(m,model,opt,8,'self')
    assert not first.exists() and not last.exists()
    assert [p for p in m.root.iterdir() if p.is_dir()]==[improved]
    assert all(e['result']=='rotated' for e in m.record['ledger'])


def test_eight_epochs_no_accumulation_stop_under_two_mib(tmp_path):
    from torch import nn
    class Padded(nn.Module):
        def __init__(self):
            super().__init__(); self.w=nn.Parameter(torch.zeros(16384))
        def forward(self,a,b): return self.w.mean().sigmoid()
    model=Padded(); opt=torch.optim.Adam(model.parameters(),lr=.01)
    b=budget(); b.update(maximum_epochs=8,early_stopping_patience_epochs=10,checkpoint_disk_limit_bytes=2*1024**2)
    state=runtime.train_loop(model,opt,rows(1,'train'),rows(1,'validation'),b,{},tmp_path/'run',17,resources=resources)
    assert state['epoch']==8 and state['status']=='complete'
    assert len(list((tmp_path/'run').glob('epoch-*')))==1
    assert tree_bytes(tmp_path/'run') < 2*1024**2


def test_resume_new_directory_shares_store_and_cumulative_disk(tmp_path):
    seed(); model=tiny(); opt=torch.optim.Adam(model.parameters(),lr=.01)
    b=budget()
    b['checkpoint_disk_limit_bytes']=2*1024**2
    runtime.train_loop(model,opt,rows(5,'train'),rows(3,'validation'),b,{},tmp_path/'first',17,resources=resources,pause_after_updates=1)
    cp=read(tmp_path/'first/latest.json')['checkpoint']
    result=runtime.train_loop(model,opt,rows(5,'train'),rows(3,'validation'),b,{},tmp_path/'second',17,resources=resources,resume=cp)
    record=read(tmp_path/'first/retention.json')
    assert len(record['segments'])==2 and result['status']=='complete'
    assert read(tmp_path/'first/latest.json')==read(tmp_path/'second/latest.json')
    assert not list((tmp_path/'second').glob('epoch-*'))
    resumed=CheckpointRetention.__new__(CheckpointRetention)
    resumed.root=tmp_path/'first'; resumed.record=record; resumed.bindings={}
    assert resumed.usage()==tree_bytes(tmp_path/'first')+tree_bytes(tmp_path/'second')
    (tmp_path/'second/unknown.bin').write_bytes(b'x'*2*1024**2)
    assert not resumed.fits(model,record['limit_bytes'])
    with pytest.raises(ValueError,match='budget changed'):
        resumed.fits(model,3*1024**2)


@pytest.mark.parametrize('failure',['write','verify','publish','references'])
def test_failed_transition_preserves_previous_good_checkpoint(tmp_path,monkeypatch,failure):
    m,model,opt=manager(tmp_path)
    old=publish(m,model,opt,0,'self')
    old_pointer=read(m.root/'latest.json')
    original_save=runtime.save_file; original_load=runtime.load_training_checkpoint
    original_replace=runtime.os.replace; original_json=runtime.atomic_json
    def broken_save(*a,**kw): raise OSError('injected write failure')
    def broken_load(*a,**kw): raise ValueError('injected verification failure')
    def broken_replace(src,dst):
        if Path(src).is_dir(): raise KeyboardInterrupt('before publication')
        return original_replace(src,dst)
    def broken_json(path,value):
        if Path(path).name=='latest.json': raise KeyboardInterrupt('after publication before reference')
        return original_json(path,value)
    if failure=='write': monkeypatch.setattr(runtime,'save_file',broken_save)
    elif failure=='verify': monkeypatch.setattr(runtime,'load_training_checkpoint',broken_load)
    elif failure=='publish': monkeypatch.setattr(runtime.os,'replace',broken_replace)
    else: monkeypatch.setattr(runtime,'atomic_json',broken_json)
    with pytest.raises((OSError,ValueError,KeyboardInterrupt)):
        publish(m,model,opt,1,'self')
    assert read(m.root/'latest.json')==old_pointer and old.is_dir()
    monkeypatch.undo()
    assert original_load(old,model,opt,m.bindings)['epoch']==0
    assert m.usage() >= tree_bytes(old)
    if failure=='references':
        new=Path(read(m.root/'retention.json')['latest'])
        assert original_load(new,model,opt,m.bindings)['epoch']==1
        out=tmp_path/'recovery'; out.mkdir()
        recovered=CheckpointRetention(out,m.bindings,resume=new)
        publish(recovered,model,opt,2,str(new))
        assert read(out/'latest.json')==read(m.root/'latest.json')


@pytest.mark.parametrize('kind',['unknown','tamper','binding','extra','external','symlink'])
def test_rotation_preserves_unknown_or_conflicting_directories(tmp_path,kind):
    m,model,opt=manager(tmp_path)
    old=publish(m,model,opt,0)
    if kind=='unknown':
        unknown=m.root/'epoch-unknown'; unknown.mkdir(); (unknown/'keep').write_text('preserve')
    elif kind=='tamper':
        with (old/'weights.safetensors').open('ab') as f: f.write(b'tamper')
    elif kind=='binding':
        manifest=read(old/'manifest.json'); manifest['bindings']={'other':True}
        runtime.atomic_json(old/'manifest.json',manifest)
    elif kind=='extra': (old/'unknown').write_text('preserve')
    elif kind=='external':
        external=tmp_path/'external'; shutil.copytree(old,external)
        m.record['entries'][0]['path']=str(external)
    else:
        external=tmp_path/'external'; external.mkdir(); (external/'keep').write_text('preserve')
        try: (old/'link').symlink_to(external,target_is_directory=True)
        except OSError:
            # Windows junctions exercise the same reparse-point refusal without symlink privileges.
            import subprocess
            subprocess.run(['cmd','/c','mklink','/J',str(old/'link'),str(external)],check=True,capture_output=True)
        with pytest.raises(ValueError,match='link or reparse'):
            publish(m,model,opt,1,'self')
        assert old.is_dir() and (external/'keep').read_text()=='preserve'
        return
    publish(m,model,opt,1,'self')
    if kind=='unknown': assert (unknown/'keep').read_text()=='preserve'
    else:
        assert old.is_dir()
        assert m.record['ledger'][-1]['result']=='preserved_conflict'
    if kind in ('external','symlink'): assert external.is_dir()


def test_link_in_destination_rejected_before_creation(tmp_path):
    external=tmp_path/'external'; external.mkdir()
    try: (tmp_path/'link').symlink_to(external,target_is_directory=True)
    except OSError:
        import subprocess
        subprocess.run(['cmd','/c','mklink','/J',str(tmp_path/'link'),str(external)],check=True,capture_output=True)
    model=tiny(); opt=torch.optim.Adam(model.parameters())
    with pytest.raises(ValueError,match='link or reparse'):
        runtime.train_loop(model,opt,rows(1,'train'),rows(1,'validation'),budget(),{},tmp_path/'link/run',17,resources=resources)
    assert not (external/'run').exists()


def test_physical_space_and_interrupted_residues_are_charged(tmp_path,monkeypatch):
    m,model,opt=manager(tmp_path)
    old=publish(m,model,opt,0,'self')
    residue=m.root/'.checkpoint-interrupted'; residue.mkdir(); (residue/'partial').write_bytes(b'x'*1024**2)
    assert not m.fits(model,2*1024**2)
    assert old.exists() and residue.exists()
    monkeypatch.setattr(shutil,'disk_usage',lambda p:type('Disk',(),{'free':1})())
    m.record.pop('limit_bytes')
    assert not m.fits(model,10*1024**2)
    assert old.exists()


def test_resume_rejects_conflicting_registry_and_tampered_bytes(tmp_path):
    m,model,opt=manager(tmp_path); cp=publish(m,model,opt,0,'self')
    out=tmp_path/'resume'; out.mkdir()
    with pytest.raises(ValueError,match='conflict'):
        CheckpointRetention(out,{'other':True},cp)
    with (cp/'local-state.pt').open('ab') as f: f.write(b'x')
    with pytest.raises(ValueError,match='altered'):
        CheckpointRetention(out,m.bindings,cp)


def test_resume_claim_cannot_use_another_compatible_execution(tmp_path):
    parent=tmp_path/'claimed'; parent.mkdir()
    m,model,opt=manager(parent)
    cp=publish(m,model,opt,0,'self')
    with pytest.raises(ValueError,match='claimed logical execution root'):
        runtime.validate_resume_claim(cp,{'first_destination':str(tmp_path/'other'),'bindings':m.bindings})


def test_ownership_rejected_even_when_manifest_hash_is_recalculated(tmp_path):
    m,model,opt=manager(tmp_path); cp=publish(m,model,opt,0)
    manifest=read(cp/'manifest.json'); manifest['ownership']['run_id']='another-run'
    runtime.atomic_json(cp/'manifest.json',manifest)
    m.record['entries'][0]['manifest_sha256']=runtime.file_hash(cp/'manifest.json')
    publish(m,model,opt,1,'self')
    assert cp.exists() and m.record['ledger'][-1]['result']=='preserved_conflict'


def test_existing_store_cannot_be_reinitialized(tmp_path):
    m,model,opt=manager(tmp_path)
    with pytest.raises(FileExistsError,match='already exists'):
        CheckpointRetention(m.root,m.bindings)
