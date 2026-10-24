import io
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hts_core.adapters import nlp
from hts_core.adapters.http import create_app
from hts_core.adapters.resources import idf_resource, load_policy
from hts_core.adapters.schemas import CompareRequest, ComparisonResult
from hts_core.adapters.semantic import ResourceUnavailable, SemanticEncoder
from hts_core.application.comparison import ComparisonService

SHARED = Path(__file__).resolve().parents[3] / 'contracts'


@pytest.fixture(scope='module')
def services():
    idf, identity = idf_resource()
    config, checksum = load_policy()
    encoder = SemanticEncoder()
    return [ComparisonService(idf, identity, enc, config, checksum, nlp.analyze, nlp.STOPWORDS, err)
            for enc, err in [(encoder, None), (None, 'cache ausente no cenário controlado')]]


def test_shared_request_fixtures():
    fixtures = json.loads((SHARED / 'requests.json').read_text(encoding='utf-8'))
    for fixture in fixtures['valid']:
        assert CompareRequest.model_validate(fixture).contract_version == '1.0'
    for fixture in fixtures['invalid']:
        with pytest.raises(ValidationError):
            CompareRequest.model_validate(fixture)


def test_shared_response_fixtures():
    fixtures = json.loads((SHARED / 'responses.json').read_text(encoding='utf-8'))
    for fixture in fixtures['valid']:
        assert ComparisonResult.model_validate(fixture).contract_version == '1.0'
    for fixture in fixtures['invalid']:
        with pytest.raises(ValidationError):
            ComparisonResult.model_validate(fixture)


def test_http_rejects_bad_contract_and_ground_truth(services):
    client = create_app(services[0]).test_client()
    for fixture in json.loads((SHARED / 'requests.json').read_text(encoding='utf-8'))['invalid']:
        response = client.post('/v1/compare', json=fixture)
        assert response.status_code == 400
        assert response.json['state'] == 'invalid_input'


def test_real_model_flow_and_best_pair_reuse(services):
    client = create_app(services[0]).test_client()
    response = client.post('/v1/compare', json={'contract_version': '1.0', 'source': {'text': 'A pesquisa compara textos.'},
                          'suspect': {'text': 'A pesquisa compara textos. A pesquisa compara textos.'}})
    assert response.status_code == 200
    result = ComparisonResult.model_validate(response.json)
    assert result.state == 'calculated'
    assert [m.source for m in result.matches] == [0, 0]
    assert [m.decision.label for m in result.matches] == ['copia_exata', 'copia_exata']
    assert len(result.alignment.pairs) == 1 and len(result.alignment.unmatched_suspect) == 1
    assert result.metadata.idf['construction_attestation'] is False
    assert result.metadata.model['revision'] == 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'


def test_missing_model_hybrid_unavailable_but_separate_lexical(services):
    client = create_app(services[1]).test_client()
    payload = {'contract_version': '1.0', 'source': {'text': 'Pesquisa textual.'}, 'suspect': {'text': 'Pesquisa textual.'}}
    response = client.post('/v1/compare', json=payload)
    assert response.json['state'] == 'resource_unavailable'
    assert response.json['index'] is None and response.json['matches'] is None
    assert response.json['lexical_index']['value'] == pytest.approx(100)
    payload['mode'] = 'lexical'
    response = client.post('/v1/compare', json=payload)
    assert response.json['state'] == 'calculated' and response.json['method'] == 'lexical'
    assert response.json['matrices']['fused'] is None


def test_valid_zero_lexical_is_flagged_without_force_100(services):
    client = create_app(services[0]).test_client()
    response = client.post('/v1/compare', json={'contract_version': '1.0', 'source': {'text': 'É o.'}, 'suspect': {'text': 'É o.'}})
    assert response.status_code == 200
    value = response.json
    assert value['matrices']['lexical'] == [[0]]
    assert value['source'][0]['flags'] == ['lexical_zero_vector']
    assert value['index']['value'] == pytest.approx(60)
    assert value['matches'][0]['decision']['label'] == 'copia_exata'


@pytest.mark.parametrize('text', [' ', '!!!'])
def test_no_useful_input_is_not_score(services, text):
    response = create_app(services[0]).test_client().post('/v1/compare', json={'contract_version': '1.0', 'source': {'text': text}, 'suspect': {'text': 'Outro texto.'}})
    assert response.status_code == 422 and response.json['state'] == 'no_useful_content'


def test_idf_failure_is_not_zero_lexical(tmp_path):
    with pytest.raises(ResourceUnavailable):
        idf_resource(tmp_path / 'missing.json')


def test_upload_txt_strict_and_unsupported(services):
    client = create_app(services[0]).test_client()
    def send(name, data):
        return client.post('/v1/extract', data={'contract_version': '1.0', 'file': (io.BytesIO(data), name)})
    assert send('texto.txt', 'Ação científica.'.encode('utf-8')).json['text'] == 'Ação científica.'
    assert send('texto.txt', 'Ação científica.'.encode('cp1252')).json['text'] == 'Ação científica.'
    assert send('invalido.txt', b'Texto \x81 fim.').json['state'] == 'extraction_failed'
    assert send('binario.bin', b'\x00\xff').json['state'] == 'unsupported_format'
    assert send('vazio.txt', b'').json['state'] == 'no_useful_content'
