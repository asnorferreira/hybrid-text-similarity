import importlib.util
import io
from pathlib import Path
import zipfile

from hts_core.adapters.http import create_app


def test_docx_malformed_xml_is_explicit_extraction_failure():
    spec=importlib.util.spec_from_file_location('ci_fixture_docx',Path(__file__).resolve().parents[2]/'scripts/gerar_fixtures_ci.py')
    generator=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    broken=io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(generator.docx_bytes())) as original, zipfile.ZipFile(broken,'w') as archive:
        for name in original.namelist():
            archive.writestr(name,b'<broken' if name=='word/document.xml' else original.read(name))
    response=create_app().test_client().post('/v1/extract',data={
        'contract_version':'1.0','file':(io.BytesIO(broken.getvalue()),'corrompido.docx')})
    assert response.status_code==422
    assert response.json['state']=='extraction_failed'
