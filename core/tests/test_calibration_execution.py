import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.calibration_resources import load_p1_resources, RESOURCE_IDENTITY
from hts_core.application.calibration_execution import run_p1
from hts_core.domain.lexical import ReferenceIdf

ROOT = Path(__file__).resolve().parents[1]


def dataset():
    sources=[];pairs=[];components={}
    for g in range(3):
        a=dict(id='a',semantic=f'Água limpa no laboratório {g}.')
        b=dict(id='b',semantic=f'Vento forte na montanha {g}.')
        source=dict(id=f's{g}',split='validation',sentences=[a,b])
        suspect=dict(id='x',semantic=a['semantic'],ancestors=[dict(source_id=source['id'],sentence_id='a')])
        pair=dict(id=f'p{g}',split='validation',source_ids=[source['id']],sentences=[suspect])
        sources.append(source);pairs.append(pair);components[pair['id']]=f'g{g}'
    pairs.append(dict(id='test',split='test'))
    return dict(sources=sources,pairs=pairs,components=components)


class Encoder:
    def __init__(self):
        self.identity=read_json(ROOT/'assets/calibration/p1-resources.json')['model_identity']
        self.calls=[]
    def encode(self,texts):
        self.calls.extend(texts)
        return np.array([[1.,0.] if t.startswith('Água') else [0.,1.] for t in texts]),[{'fixture':True}]


def resources(encoder):
    return (ReferenceIdf(3,{},'fixture'),read_json(ROOT/'configs/comparison.json'),
            read_json(ROOT/'assets/calibration/p1-resources.json'))


def test_runner_validation_only_caches_texts_reloads_and_writes_reliability(tmp_path):
    encoder=Encoder();config=read_json(ROOT/'configs/experiment_s5b.r3.json')
    result=run_p1(dataset(),encoder,config,{'fixture':'runner'},tmp_path/'p1',
                  resource_loader=resources,resources=lambda:dict(rss_bytes=1))
    assert result['counts']['eligible']==6 and result['counts']['components']==3
    assert len(encoder.calls)==len(set(encoder.calls))==6
    assert result['reload_verification']['loaded'] and result['reload_verification']['maximum_error']==0
    assert result['evaluation']['status']=='evaluated_out_of_fold'
    assert result['q5v2_decision']['metrics']['n']==6 and not result['test_used']
    for path in (tmp_path/'p1').glob('*.svg'):
        assert ET.parse(path).getroot().tag.endswith('svg')
        assert 'n por faixa' in path.read_text()
    assert len(list((tmp_path/'p1').glob('*.svg')))==3
    stored=json.loads((tmp_path/'p1/result.json').read_text())
    assert stored['fit_diagnostics']['scope']=='resubstitution_diagnostic_not_independent'


def test_real_application_resources_match_rg01_and_reject_model_drift():
    encoder=Encoder()
    _,_,frozen=load_p1_resources(encoder)
    assert frozen['identity']==RESOURCE_IDENTITY
    encoder.identity=copy.deepcopy(encoder.identity);encoder.identity['revision']='changed'
    with pytest.raises(ValueError,match='differ'):load_p1_resources(encoder)


@pytest.mark.parametrize('kind',['wall','rss'])
def test_runner_resource_limits_before_inference(tmp_path,kind):
    encoder=Encoder();config=read_json(ROOT/'configs/experiment_s5b.r3.json')
    kwargs=dict(started=0,clock=lambda:601,resources=lambda:dict(rss_bytes=1)) if kind=='wall' else dict(resources=lambda:dict(rss_bytes=4*1024**3))
    with pytest.raises((TimeoutError,MemoryError)):
        run_p1(dataset(),encoder,config,{'fixture':'limit'},tmp_path/'p1',resource_loader=resources,**kwargs)
    assert encoder.calls==[] and not (tmp_path/'p1/platt.json').exists()
