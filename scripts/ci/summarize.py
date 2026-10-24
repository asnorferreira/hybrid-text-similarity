import json
import os
from pathlib import Path
import subprocess

folder=Path('core/artifacts/ci/results')
record={'purpose':'engineering development validation; not research evaluation',
        'checked_out_sha':subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
        'event':os.environ.get('CI_EVENT_NAME','local'),
        'event_sha':os.environ.get('CI_EVENT_SHA'), 'head_sha':os.environ.get('CI_HEAD_SHA'),
        'core':json.loads((folder/'runtime-core.json').read_text()),
        'web':json.loads((folder/'runtime-web.json').read_text())}
(folder/'technical.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
