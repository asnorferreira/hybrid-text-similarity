import argparse
import hashlib
import json
from pathlib import Path
from hts_core.adapters.dataset_formats import render

CORE=Path(__file__).resolve().parents[1]
PAIRS=CORE/'tests/fixtures/equivalence/pairs.json'

def generate(out):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    pairs=json.loads(PAIRS.read_text())['pairs']
    files={}
    for relation,pair in pairs.items():
        for role in ('source','suspect'):
            for kind in ('txt','docx','pdf'):
                payload,metadata=render(pair[role],kind)
                name=f'{relation}-{role}.{kind}'
                target=out/name
                if target.exists() and target.read_bytes()!=payload:
                    raise ValueError(f'fixture exists with different bytes: {name}; preserve it and use a new output')
                target.write_bytes(payload)
                files[name]={'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload),'format':metadata}
    manifest={'schema':'hts-equivalence-formats-1','research_data_used':False,
              'pairs_sha256':hashlib.sha256(PAIRS.read_bytes()).hexdigest(),'files':files}
    payload=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    target=out/'manifest.json'
    if target.exists() and target.read_bytes()!=payload:
        raise ValueError('manifest differs; preserve previous output')
    target.write_bytes(payload)
    return {'files':len(files),'research_data_used':False,'manifest_sha256':hashlib.sha256(payload).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Gerar fixtures de equivalência.')
    parser.add_argument('--out',type=Path,required=True)
    print(json.dumps(generate(parser.parse_args().out)))
