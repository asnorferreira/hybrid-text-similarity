from tests.http_support import json_object
import io
import json
import math
import sys

from hts_core.adapters.http import create_app
from hts_core.adapters.schemas import Extraction


def test_engineering_headers_keep_json_contract_and_explicit_memory_scope():
    response = create_app().test_client().post('/v1/extract', data={
        'contract_version': '1.0', 'file': (io.BytesIO('Pesquisa válida.'.encode()), 'texto.txt')})
    assert response.status_code == 200
    assert Extraction.model_validate(json_object(response)).text == 'Pesquisa válida.'
    assert set(json_object(response)) == {'contract_version', 'text'}
    elapsed = float(response.headers['Server-Timing'].split('dur=')[1])
    assert math.isfinite(elapsed) and elapsed >= 0
    if sys.platform == 'win32':
        assert 'X-HTS-Process-Peak-RSS-KiB' not in response.headers
    else:
        assert int(response.headers['X-HTS-Process-Peak-RSS-KiB']) > 0


def test_extraction_notes_report_observed_cleanup_without_changing_body_schema():
    response = create_app().test_client().post('/v1/extract', data={
        'contract_version': '1.0', 'file': (io.BytesIO('Uma pala\u00advra.'.encode()), 'texto.txt')})
    assert json_object(response) == {'contract_version': '1.0', 'text': 'Uma palavra.'}
    assert json.loads(response.headers['X-HTS-Extraction-Notes']) == {
        'format': 'txt', 'cleanup_changed': True, 'soft_hyphen_observed': True, 'hyphen_linebreak_observed': False}
