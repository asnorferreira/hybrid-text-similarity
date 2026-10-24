import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import threading
import time

import pytest
from pydantic import ValidationError

from hts_core.adapters import nlp
from hts_core.adapters import http
from hts_core.adapters.http import create_app
from hts_core.adapters.resources import idf_resource, load_policy
from hts_core.adapters.schemas import CompareRequest, ComparisonResult
from hts_core.adapters.semantic import ResourceUnavailable, SemanticEncoder
from hts_core.application.comparison import ComparisonService
from hts_core.domain.strings import levenshtein

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


def test_html_looking_text_is_literal_content_not_markup(services):
    response = create_app(services[0]).test_client().post('/v1/compare', json={
        'contract_version': '1.0', 'source': {'text': '<b></b>'}, 'suspect': {'text': '<b></b>'}})
    assert response.status_code == 200
    assert response.json['source'][0]['raw'] == '<b></b>'
    assert response.json['source'][0]['semantic'] == '<b></b>'
    assert response.json['source'][0]['flags'] == ['lexical_zero_vector']
    assert response.json['lexical_index']['value'] == 0
    assert response.json['index']['value'] == pytest.approx(60)


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


def test_phase_headers_are_optional_to_body_and_match_executed_stages(services):
    client = create_app(services[0]).test_client()
    body = {'contract_version': '1.0', 'source': {'text': 'Uma pesquisa válida.'}, 'suspect': {'text': 'Outra pesquisa válida.'}}
    for mode in ['lexical', 'hybrid']:
        response = client.post('/v1/compare', json={**body, 'mode': mode})
        assert response.status_code == 200
        ComparisonResult.model_validate(response.json)
        stages = {part.strip().split(';dur=')[0]: float(part.strip().split(';dur=')[1])
                  for part in response.headers['Server-Timing'].split(',')}
        expected = {'resources', 'compare', 'preprocess', 'lexical'}
        if mode == 'hybrid':
            expected |= {'embeddings', 'matrices', 'alignment', 'pairs'}
        assert set(stages) == expected
        assert all(value >= 0 for value in stages.values())
        assert 'engineering' not in response.json['metadata']


def test_character_score_is_computed_once_and_reused_for_classification(services):
    count = 0
    def observe(frame, event, arg):
        nonlocal count
        if event == 'call' and frame.f_code is levenshtein.__code__:
            count += 1
    previous = sys.getprofile()
    try:
        sys.setprofile(observe)
        response = create_app(services[0]).test_client().post('/v1/compare', json={
            'contract_version': '1.0', 'source': {'text': 'abcde'}, 'suspect': {'text': 'abcdX'}})
    finally:
        sys.setprofile(previous)
    assert response.status_code == 200
    match = response.json['matches'][0]
    assert match['edit'] == pytest.approx(4 / 5)
    assert match['characters']['levenshtein'] == pytest.approx(4 / 5)
    assert count == 1


def test_resource_initialization_is_serialized_but_lexical_calculation_is_real(services, monkeypatch):
    count = 0
    def unavailable_model():
        nonlocal count
        count += 1
        time.sleep(.1)
        raise ResourceUnavailable('modelo ausente no cenário controlado de inicialização')
    monkeypatch.setattr(http, 'idf_resource', lambda path: (services[0].idf, services[0].idf_info))
    monkeypatch.setattr(http, 'SemanticEncoder', unavailable_model)
    app = create_app()
    barrier = threading.Barrier(2)
    def compare(_):
        barrier.wait()
        with app.test_client() as client:
            return client.post('/v1/compare', json={'contract_version': '1.0', 'mode': 'lexical',
                'source': {'text': 'Pesquisa válida.'}, 'suspect': {'text': 'Pesquisa válida.'}})
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(compare, range(2)))
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json['index']['value'] == pytest.approx(100) for response in responses)
    assert count == 1
