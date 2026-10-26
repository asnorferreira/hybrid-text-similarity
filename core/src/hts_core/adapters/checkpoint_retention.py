from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import stat
import uuid

from hts_core.adapters.dataset_store import identity

POLICY = 'latest-and-selected-owned-v2'


def safe_path(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        if parent.exists() or parent.is_symlink():
            info = parent.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('checkpoint path contains a link or reparse point')
    return path


def tree_bytes(path):
    path = safe_path(path)
    if path.is_file():
        return path.stat().st_size
    return sum(tree_bytes(Path(entry.path)) for entry in os.scandir(path))


class CheckpointRetention:
    def __init__(self, destination, bindings, resume=None):
        from hts_core.adapters.training_runtime import atomic_json, file_hash
        self.out = safe_path(destination)
        self.bindings = bindings
        if resume is None:
            self.root = self.out
            if (self.root/'retention.json').exists() or (self.root/'logical-execution.json').exists():
                raise FileExistsError('logical checkpoint store already exists')
            self.record = {'schema':'hts-checkpoint-retention-2','policy':POLICY,
                           'run_id':uuid.uuid4().hex,'root':str(self.root),
                           'bindings':bindings,'bindings_identity':identity(bindings),
                           'segments':[str(self.out)],'entries':[], 'latest':None,'selected':None,'ledger':[]}
        else:
            cp = safe_path(resume)
            manifest = json.loads((cp/'manifest.json').read_text(encoding='utf-8'))
            owner = manifest.get('ownership', {})
            self.root = safe_path(owner['root'])
            self.record = json.loads(safe_path(self.root/'retention.json').read_text(encoding='utf-8'))
            if (self.record['schema'] != 'hts-checkpoint-retention-2' or self.record['policy'] != POLICY
                    or self.record['root'] != str(self.root) or self.record['bindings'] != bindings
                    or self.record['bindings_identity'] != identity(bindings)
                    or owner != self.owner or self.record['latest'] != str(cp)):
                raise ValueError('resume retention ownership/latest conflict')
            self.verify_entry(next(e for e in self.record['entries'] if e['path']==str(cp)))
            if self.out != self.root and self.root in self.out.parents:
                raise ValueError('resume destination must not nest in checkpoint root')
            self.record['segments'].append(str(self.out))
        for segment in self.record['segments'][:-1]:
            marker=json.loads((safe_path(segment)/'logical-execution.json').read_text(encoding='utf-8'))
            if marker != self.owner:
                raise ValueError('logical execution segment ownership conflict')
        atomic_json(self.out/'logical-execution.json', self.owner)
        self.commit()

    @property
    def owner(self):
        return {k:self.record[k] for k in ('root','run_id','policy','bindings_identity')}

    def commit(self):
        from hts_core.adapters.training_runtime import atomic_json
        safe_path(self.root/'retention.json')
        atomic_json(self.root/'retention.json',self.record)

    def path(self, state):
        n=len(self.record['entries'])
        return self.root/(f"epoch-{state['epoch']:03}-cursor-{state['cursor']:05}-update-{state['updates']:06}-snapshot-{n:04}")

    def usage(self):
        segments=[safe_path(p) for p in self.record['segments']]
        if len(set(segments)) != len(segments) or any(a in b.parents for a in segments for b in segments if a != b):
            raise ValueError('overlapping logical execution segments')
        for p in segments:
            if json.loads((p/'logical-execution.json').read_text(encoding='utf-8')) != self.owner:
                raise ValueError('logical execution segment ownership conflict')
        return sum(tree_bytes(p) for p in segments)

    def estimate(self, model):
        initial=sum(p.numel()*p.element_size() for p in model.state_dict().values())*4+1024**2
        observed=max((e.get('bytes',0) for e in self.record['entries']),default=0)
        return max(initial, int(observed*1.1)+65536)

    def fits(self, model, limit):
        if 'limit_bytes' in self.record and self.record['limit_bytes'] != limit:
            raise ValueError('logical checkpoint disk budget changed on resume')
        self.record['limit_bytes']=limit
        estimate=self.estimate(model)
        used=self.usage()
        free=shutil.disk_usage(self.root).free
        self.record['disk']={'used_bytes':used,'estimated_transition_bytes':estimate,
                             'physical_free_bytes':free,'limit_bytes':limit,
                             'scope':'all registered logical execution segments including unknown files and interrupted temporaries'}
        self.commit()
        return used+estimate <= limit and free >= estimate

    def verify_entry(self, entry):
        from hts_core.adapters.training_runtime import file_hash
        cp=safe_path(entry['path'])
        if cp.parent != self.root or entry['status'] != 'live':
            raise ValueError('checkpoint inventory ownership conflict')
        manifest=json.loads((cp/'manifest.json').read_text(encoding='utf-8'))
        if (file_hash(cp/'manifest.json') != entry['manifest_sha256'] or manifest.get('ownership') != self.owner
                or manifest['bindings'] != self.bindings or manifest['bindings_identity'] != identity(self.bindings)
                or set(manifest['files']) != {'weights.safetensors','local-state.pt'}
                or {p.name for p in cp.iterdir()} != {'manifest.json','weights.safetensors','local-state.pt'}):
            raise ValueError('checkpoint inventory/manifest conflict')
        for name, digest in manifest['files'].items():
            if file_hash(safe_path(cp/name)) != digest:
                raise ValueError('checkpoint bytes altered')
        return cp, manifest

    def publish(self, cp, model, optimizer, state, limit):
        from hts_core.adapters.training_runtime import atomic_json, file_hash, save_training_checkpoint
        cp=safe_path(cp)
        if cp != self.path(state):
            raise ValueError('checkpoint destination differs from owned inventory')
        entry={'path':str(cp),'status':'pending'}
        self.record['entries'].append(entry)
        self.commit()
        manifest=save_training_checkpoint(cp,model,optimizer,state,self.bindings,ownership=self.owner)
        entry.update(status='live',manifest_sha256=file_hash(cp/'manifest.json'),bytes=tree_bytes(cp))
        self.verify_entry(entry)
        if self.usage() > limit:
            self.record['ledger'].append({'event':'observed_disk_exceeded','path':str(cp),'bytes':entry['bytes']})
            self.commit()
            raise OSError('observed checkpoint exceeds logical disk budget; previous references preserved')
        selected=state['best_checkpoint']
        if selected is not None:
            self.verify_entry(next(e for e in self.record['entries'] if e['path']==selected))
        self.record.update(latest=str(cp),selected=selected)
        self.commit()
        for segment in self.record['segments']:
            atomic_json(Path(segment)/'latest.json',{'checkpoint':str(cp),'selected':selected,
                         'manifest_sha256':entry['manifest_sha256'],'retention_root':str(self.root)})
        self.rotate()
        self.record['disk']['observed_checkpoint_bytes']=entry['bytes']
        self.record['disk']['observed_after_rotation_bytes']=self.usage()
        self.commit()
        return manifest

    def rotate(self):
        keep={self.record['latest'],self.record['selected']}
        for entry in self.record['entries']:
            if entry['status'] != 'live' or entry['path'] in keep:
                continue
            event={'path':entry['path'],'manifest_sha256':entry['manifest_sha256'],
                   'replacement':self.record['latest'],'reason':'verified latest and selected published',
                   'utc':datetime.now(timezone.utc).isoformat()}
            try:
                cp,manifest=self.verify_entry(entry)
            except (OSError,ValueError,KeyError) as exc:
                event.update(result='preserved_conflict',detail=str(exc))
                self.record['ledger'].append(event); self.commit()
                continue
            event.update(result='authorized',files=manifest['files'])
            self.record['ledger'].append(event); self.commit()
            for name in ('weights.safetensors','local-state.pt','manifest.json'):
                (cp/name).unlink()
            cp.rmdir()
            entry['status']='rotated'
            event['result']='rotated'
            self.commit()
