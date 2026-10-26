import importlib.util
import io
from pathlib import Path
import socket
import zipfile

import pytest

from hts_core.adapters.parsers import parse_document


def package(extra_name=None, extra_bytes=b'', document=None):
    spec = importlib.util.spec_from_file_location('public_docx', Path(__file__).resolve().parents[2] / 'scripts/gerar_fixtures_ci.py')
    assert spec is not None and spec.loader is not None
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    output = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(generator.docx_bytes())) as original, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in original.namelist():
            archive.writestr(name, document if name == 'word/document.xml' and document else original.read(name))
        if extra_name:
            archive.writestr(extra_name, extra_bytes)
    return output.getvalue()


def test_docx_expansion_is_bounded_before_loading():
    with pytest.raises(ValueError):
        parse_document('grande.docx', package('payload.bin', b'A' * (21 * 1024 * 1024)))


def test_docx_traversal_member_is_refused_without_extracting():
    with pytest.raises(ValueError):
        parse_document('caminho.docx', package('../unused.bin', b'public sentinel'))


def test_docx_doctype_is_refused_without_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('XML não deve abrir conexão')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    document = b'''<!DOCTYPE w:document [<!ENTITY x SYSTEM "http://127.0.0.1:9/not-used">]>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>
    <w:p><w:r><w:t>&x;</w:t></w:r></w:p></w:body></w:document>'''
    with pytest.raises(ValueError):
        parse_document('entidade.docx', package(document=document))
