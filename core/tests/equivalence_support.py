from tests.http_support import json_object
import io
import json
from pathlib import Path

from hts_core.adapters import nlp
from hts_core.adapters.http import create_app
from hts_core.adapters.resources import idf_resource,load_policy
from hts_core.adapters.semantic import SemanticEncoder
from hts_core.application.comparison import ComparisonService

FIXTURES=Path(__file__).parent/'fixtures/equivalence'
PAIRS=json.loads((FIXTURES/'pairs.json').read_text())['pairs']
FORMATS=('txt','docx','pdf','pasted')
MODES=('hybrid','lexical')
STRONG=[(f'NFo-{i:02}',kind,mode,relation)
        for i,(kind,mode,relation) in enumerate(((k,m,r) for k in FORMATS for m in MODES for r in PAIRS),1)]

def make_service(encoder=True):
    table,identity=idf_resource();policy,checksum=load_policy()
    return ComparisonService(table,identity,SemanticEncoder() if encoder else None,
                             policy,checksum,nlp.analyze,nlp.STOPWORDS,
                             None if encoder else 'modelo ausente no cenário de equivalência')

def client_for(service): return create_app(service).test_client()

def payload(source,suspect,mode='hybrid'):
    return {'contract_version':'1.0','source':{'text':source},'suspect':{'text':suspect},'mode':mode}

def extract(client,name,data,**fields):
    return client.post('/v1/extract',data={'contract_version':'1.0','file':(io.BytesIO(data),name),**fields})

def strong_response(client,kind,mode,relation):
    pair=PAIRS[relation];texts={}
    for role in ('source','suspect'):
        if kind=='pasted': texts[role]=pair[role]
        else:
            response=extract(client,f'{relation}-{role}.{kind}',(FIXTURES/'formats'/f'{relation}-{role}.{kind}').read_bytes())
            assert response.status_code==200,json_object(response)
            texts[role]=json_object(response)['text']
            assert texts[role]==pair[role]
    response=client.post('/v1/compare',json=payload(texts['source'],texts['suspect'],mode))
    assert response.status_code==200,json_object(response)
    return json_object(response)

def projection(result):
    return {key:result[key] for key in ('state','method','index','lexical_index','semantic_index',
                                       'matrices','source','suspect','matches','alignment','summary')}
