import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'core/src'))
from hts_core.adapters.training_contract import memory_snapshot


def stack_state():
    names = [f'hybrid-text-similarity-{s}-1' for s in ('mongo','core','web')]
    result = subprocess.run(['docker','inspect','--format','{{json .State}}',*names],
                            check=True, capture_output=True, text=True)
    states = [json.loads(line) for line in result.stdout.splitlines()]
    if len(states) != 3 or any(not s['Running'] for s in states):
        raise RuntimeError('all three existing stack services must be running')
    if any(s.get('Health',{}).get('Status') != 'healthy' for s in states[:2]):
        raise RuntimeError('MongoDB/core must be healthy')
    return {n:{'running':s['Running'],'health':s.get('Health',{}).get('Status','not_configured')}
            for n,s in zip(names,states,strict=True)}


def main():
    parser = argparse.ArgumentParser(description='Executar S5B em Docker.')
    parser.add_argument('operation', choices=('readiness','run'))
    parser.add_argument('--task',choices=('H1','H2'),required=True)
    parser.add_argument('--destination',required=True,help='new relative directory under core/artifacts/s5b-docker-01')
    parser.add_argument('--resume',help='own compatible /s5b-output checkpoint path')
    args = parser.parse_args()
    if sys.platform != 'win32':
        raise RuntimeError('this host probe requires Windows; use an explicitly validated host collector elsewhere')
    relative = Path(args.destination)
    if relative.is_absolute() or '..' in relative.parts or len(relative.parts) != 1:
        raise ValueError('destination must be a new single directory name')
    output = ROOT/'core/artifacts/s5b-docker-01'
    output.mkdir(exist_ok=True)
    if (output/relative).exists():
        raise FileExistsError('experiment output already exists; choose a new segment')
    name = 'hts-s5b-'+args.task.lower()+'-'+uuid.uuid4().hex[:12]
    stamp = output/(relative.name+'-launcher.json')
    if stamp.exists():
        raise FileExistsError(stamp)
    lock = output/'host-monitor.lock'
    with lock.open('x') as stream:
        stream.write(name)
    record = {'task':args.task,'operation':args.operation,'container':name,'started_utc':datetime.now(timezone.utc).isoformat(),
              'training_location':'Docker only','host_samples':[],'stack_samples':[]}
    try:
        command = ['docker','compose','-f','docker-compose.s5b.yml','-p','hts-s5b-docker',
                   'run','--no-deps','--name',name,'training','python','-m','hts_core.cli','training',args.operation,
                   '--protocol','configs/experiment_s5b.json','--reference','configs/experiment_s5a.json',
                   '--dataset','artifacts/s4-fechamento-01/frozen-curated-01',
                   '--idf','artifacts/s4-fechamento-01/idf-final-01',
                   '--annotations',f'artifacts/s5b-01/annotations-{args.task}.json',
                   '--campaign','artifacts/s5b-01','--task',args.task,
                   '--out','/s5b-output/'+relative.name]
        if args.resume:
            if not args.resume.startswith('/s5b-output/') or '..' in Path(args.resume).parts:
                raise ValueError('resume must reference own persistent checkpoint')
            command += ['--resume',args.resume]
        record['command'] = command
        def sample():
            record['stack_samples'].append({'utc':datetime.now(timezone.utc).isoformat(),'services':stack_state()})
            host = memory_snapshot()
            host['utc'] = datetime.now(timezone.utc).isoformat()
            record['host_samples'].append(host)
            pending = output/'host-memory-live.pending'
            pending.write_text(json.dumps(host),encoding='utf-8')
            pending.replace(output/'host-memory-live.json')
        sample()
        with (output/(relative.name+'-console.log')).open('x',encoding='utf-8') as log:
            process = subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:
                while process.poll() is None:
                    time.sleep(5)
                    sample()
            except BaseException:
                subprocess.run(['docker','stop','--time','30',name],capture_output=True)
                process.wait()
                raise
            record['exit_code'] = process.returncode
        record['final_stack'] = stack_state()
        print(json.dumps({'container':name,'exit_code':record['exit_code'],'receipt':str(stamp)}))
        return record['exit_code']
    except BaseException as exc:
        record['failure'] = {'type':type(exc).__name__,'message':str(exc)}
        raise
    finally:
        record['ended_utc'] = datetime.now(timezone.utc).isoformat()
        stamp.write_text(json.dumps(record,indent=2),encoding='utf-8')
        lock.unlink()


if __name__ == '__main__':
    sys.exit(main())
