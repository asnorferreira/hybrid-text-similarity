from tests.http_support import json_object
from copy import copy
import io
import json

import numpy as np
import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from hts_core.adapters.dataset_formats import render
from tests.equivalence_support import (PAIRS,STRONG,client_for,extract,make_service,payload,projection,strong_response)

@pytest.fixture(scope='module')
def service(): return make_service()

@pytest.fixture(scope='module')
def client(service): return client_for(service)

@pytest.fixture(scope='module')
def strong(client):
    return {case:strong_response(client,kind,mode,relation) for case,kind,mode,relation in STRONG}

def assert_same(actual,expected):
    if isinstance(expected,dict):
        assert actual.keys()==expected.keys()
        for key in expected: assert_same(actual[key],expected[key])
    elif isinstance(expected,list):
        assert len(actual)==len(expected)
        for a,b in zip(actual,expected,strict=True): assert_same(a,b)
    elif isinstance(expected,float): assert actual==pytest.approx(expected,abs=1e-9,rel=0)
    else: assert actual==expected

@pytest.mark.parametrize('case,kind,mode,relation',STRONG,ids=[r[0] for r in STRONG])
def test_normal_strong(case,kind,mode,relation,strong,record_property):
    result=strong[case]
    baseline=next(id_ for id_,k,m,r in STRONG if k=='pasted' and m==mode and r==relation)
    assert_same(projection(result),projection(strong[baseline]))
    assert result['state']=='calculated' and result['index'] is not None
    if mode=='hybrid':
        assert {m['decision']['label'] for m in result['matches']}=={PAIRS[relation]['expected_hybrid']}
    else:
        assert result['semantic_index'] is None
        assert all(result['matrices'][key] is None for key in ('semantic_raw','semantic_operational','fused'))
        hybrid=next(id_ for id_,k,m,r in STRONG if k==kind and m=='hybrid' and r==relation)
        assert_same(result['lexical_index'],strong[hybrid]['lexical_index'])
        assert result['matches'] is None
        record_property('lexical_class','indisponivel_pelo_contrato_sem_semantica')
    record_property('equivalence_id',case)

def send_pair(client,source,suspect,kind='pasted',mode='hybrid',encoding='utf-8',padding=None):
    texts=[]
    for role,text in [('source',source),('suspect',suspect)]:
        if kind!='pasted':
            data=text.encode(encoding) if kind=='txt' else render(text,kind)[0]
            if padding is not None:
                data+=b' '*(padding-len(data))
                assert len(data)==padding
            response=extract(client,role+'.'+kind,data)
            assert response.status_code==200,json_object(response)
            text=json_object(response)['text']
        texts.append(text)
    return client.post('/v1/compare',json=payload(texts[0],texts[1],mode))

def boundary_text(length,count):
    available=length-(count-1)
    parts=[]
    for i in range(count):
        n=available//count+(i<available%count)
        body=('Pesquisa científica documentada '*((n//30)+2))[:n-1].rstrip()
        body+=('x'*(n-1-len(body)))
        parts.append(body+'.')
    text=' '.join(parts)
    assert len(text)==length
    return text

@pytest.mark.parametrize('case',[f'NF-{i:02}' for i in range(1,13)])
def test_normal_weak(case,client,record_property):
    kind='pasted';mode='hybrid';encoding='utf-8';padding=None
    if case in ('NF-01','NF-05','NF-06'):
        source=boundary_text(500,5);suspect=source
        kind='txt';encoding={'NF-01':'utf-8','NF-05':'utf-8-sig','NF-06':'cp1252'}[case]
        if case=='NF-06': mode='lexical';suspect=source.replace('Pesquisa','Pesquiza')
    elif case=='NF-02':
        source=boundary_text(2000,20);suspect=source.replace('Pesquisa','Pesquiza');kind='docx'
    elif case in ('NF-03','NF-04'):
        relation='R3' if case=='NF-03' else 'R4';source=PAIRS[relation]['source'];suspect=PAIRS[relation]['suspect']
        kind='pdf' if case=='NF-03' else 'pasted';mode='hybrid' if case=='NF-03' else 'lexical'
    elif case=='NF-07':
        source=suspect='\n\n'.join(['العلم يساعد الناس في فهم العالم.']*10);kind='docx'
    elif case=='NF-08':
        # Numbered CJK content exercises the documented digit boundary rule;
        # this is not a claim of general Chinese punctuation segmentation.
        source=' '.join(f'{i} 医生在医院治疗病人.' for i in range(1,11))
        suspect=' '.join(f'{i} 患者在医疗机构接受大夫的诊治.' for i in range(1,11));kind='pdf'
    elif case=='NF-09': source=suspect='A'
    elif case=='NF-10':
        source=boundary_text(30000,120);suspect=source.replace('Pesquisa','Pesquiza');mode='lexical'
    elif case=='NF-11':
        source=PAIRS['R4']['source'];suspect=PAIRS['R4']['suspect'];kind='txt';mode='lexical';padding=5242880
    else:
        source=boundary_text(4000,1);suspect=source.replace('Pesquisa','Pesquiza',1)
    response=send_pair(client,source,suspect,kind,mode,encoding,padding)
    assert response.status_code==200,json_object(response)
    result=json_object(response)
    assert result['state']=='calculated' and np.isfinite(result['index']['value'])
    if case in ('NF-01','NF-05'): assert result['index']['value']==pytest.approx(100,abs=1e-9)
    if case in ('NF-02','NF-12'): assert {m['decision']['label'] for m in result['matches']}=={'copia_editada'}
    if case=='NF-03': assert result['matches'][0]['decision']['label']=='parafrase'
    if case in ('NF-04','NF-06','NF-10','NF-11'): assert result['semantic_index'] is None
    if case in ('NF-07','NF-08'): assert len(result['source'])==len(result['suspect'])==10
    if case=='NF-05': assert all('\ufeff' not in s['semantic'] for s in result['source'])
    if case=='NF-06': assert 'científica' in result['source'][0]['semantic']
    if case=='NF-09': assert len(result['source'][0]['semantic'])==1
    if case=='NF-10': assert len(source)==30000 and len(result['source'])==120
    if case=='NF-12': assert len(result['source'])==1 and len(result['source'][0]['semantic'])==4000
    record_property('equivalence_id',case)
    record_property('actual_source_characters',len(source))
    record_property('actual_source_sentences',len(result['source']))


def scanned_pdf():
    stream=io.BytesIO();page=canvas.Canvas(stream,invariant=1)
    page.drawImage(ImageReader(Image.new('RGB',(30,30),'black')),72,600)
    page.save();return stream.getvalue()

ROBUST=[f'RF-{i:02}' for i in range(1,22)]+['RF-26']
@pytest.mark.parametrize('case',ROBUST)
def test_robust_weak(case,client,service,record_property):
    body=payload(PAIRS['R1']['source'],PAIRS['R1']['suspect'])
    expected_status=422;expected_state='invalid_input';response=None
    upload={
      'RF-01':('false.txt',render('Texto válido.','pdf')[0],415,'unsupported_format'),
      'RF-02':('document.odt',b'Texto valido.',415,'unsupported_format'),
      'RF-03':('scan.pdf',scanned_pdf(),422,'extraction_failed'),
      'RF-04':('truncated.docx',b'PK\x03\x04truncated',422,'extraction_failed'),
      'RF-05':('empty.txt',b'',422,'no_useful_content'),
      'RF-06':('large.txt',b'x'*5242881,413,'invalid_input'),
      'RF-11':('invalid.txt',b'\x81',422,'extraction_failed'),
      'RF-12':('invalid-bom.txt',b'\xef\xbb\xbf\x81',422,'extraction_failed')}
    if case in upload:
        name,data,expected_status,expected_state=upload[case];response=extract(client,name,data)
    elif case=='RF-07': body['source']['text']=' \n\t ';expected_state='no_useful_content'
    elif case=='RF-08': body['source']['text']='x'*30001
    elif case=='RF-09': body['source']['text']=' '.join(['Pesquisa válida.']*121)
    elif case=='RF-10': body['source']['text']='x'*4001
    elif case in ('RF-13','RF-14','RF-15','RF-16','RF-17','RF-18'):
        expected_status=400
        if case=='RF-13': body['mode']='inventado'
        elif case=='RF-14': body['contract_version']='2.0'
        elif case=='RF-15': body['source']['r']=1
        elif case=='RF-16': body['origin']='generator'
        elif case=='RF-17': del body['suspect']
        else: body['source']['text']=12
    elif case in ('RF-19','RF-20'):
        missing=copy(service);missing.encoder=None;missing.semantic_error='modelo ausente'
        if case=='RF-20': body['mode']='lexical'
        response=client_for(missing).post('/v1/compare',json=body)
        if case=='RF-20':
            assert response.status_code==200 and json_object(response)['state']=='calculated'
            assert json_object(response)['index']['value']==pytest.approx(100,abs=1e-9)
            assert json_object(response)['semantic_index'] is None
            record_property('equivalence_id',case)
            return
        expected_status=503;expected_state='resource_unavailable'
    elif case=='RF-21':
        # 8 valid sentences, each <4000 chars, document <30000; only the
        # complete content-token budget is invalid. Count with the real tokenizer.
        sentence='Pesquisa '+'甲乙 '*900+'.'
        text='\n\n'.join([sentence]*8)
        assert len(text)<30000 and len(sentence)<4000
        assert sum(len(service.encoder.tokens(s)) for s in text.split('\n\n'))>12000
        body['source']['text']=text;expected_status=503;expected_state='resource_unavailable'
    else:
        response=extract(client,'valid.txt',b'Pesquisa valida.',foo='extra')
        expected_status=400
    if response is None: response=client.post('/v1/compare',json=body)
    assert response.status_code==expected_status,json_object(response)
    assert json_object(response)['state']==expected_state
    assert not {'index','matches','summary','class','result'}.intersection(json_object(response))
    if case=='RF-03': assert 'OCR' in json_object(response)['detail']
    if case=='RF-21': assert 'sem classificação' in json_object(response)['detail']
    record_property('equivalence_id',case)
