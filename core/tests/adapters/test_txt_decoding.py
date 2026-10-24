import codecs

import pytest

from hts_core.adapters.parsers import parse_document
from hts_core.adapters.parsers.txt_parser import extract_txt_text


@pytest.mark.parametrize("data", [
    b"Texto \x81 fim.",
    b"Texto \x8d fim.",
    codecs.BOM_UTF8 + b"Texto \xff fim.",
])
def test_invalid_encoding_is_reported_without_replacement(data):
    with pytest.raises(ValueError, match="decodificar TXT") as error:
        extract_txt_text(data)
    assert isinstance(error.value.__cause__, UnicodeDecodeError)
    with pytest.raises(ValueError, match="decodificar TXT"):
        parse_document("entrada.txt", data)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "cp1252"])
def test_supported_encodings_preserve_exact_characters(encoding):
    text = "Informação: ação, café, € e ‘aspas’."
    data = text.encode(encoding)
    assert extract_txt_text(data) == text
    assert parse_document("entrada.txt", data) == text
