import importlib.util
import io
from pathlib import Path
import zipfile

from hts_core.adapters.parsers import parse_document

spec=importlib.util.spec_from_file_location('ci_fixtures',Path(__file__).resolve().parents[2]/'scripts/gerar_fixtures_ci.py')
assert spec is not None and spec.loader is not None
generator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


def test_generated_public_fixtures_are_deterministic_and_have_independent_expected_text(tmp_path):
    a,b=tmp_path/'a',tmp_path/'b'
    generator.generate(a)
    generator.generate(b)
    assert {p.name:p.read_bytes() for p in a.iterdir()}=={p.name:p.read_bytes() for p in b.iterdir()}
    assert b'algo\\255ritmo' in (a/'tipo1-perda.pdf').read_bytes()
    assert parse_document('tipo1-perda.pdf',(a/'tipo1-perda.pdf').read_bytes())=='O algoritmo funciona.'
    assert parse_document('texto.docx',(a/'texto.docx').read_bytes()).splitlines()==['A informação chegou.','','O guarda-chuva chegou.']


def test_docx_fixture_fixes_zip_creator_platform():
    with zipfile.ZipFile(io.BytesIO(generator.docx_bytes())) as archive:
        assert all(entry.create_system == 3 for entry in archive.infolist())
