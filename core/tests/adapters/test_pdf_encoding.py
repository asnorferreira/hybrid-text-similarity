from concurrent.futures import ThreadPoolExecutor

from pdfminer.encodingdb import EncodingDB
import pytest

from hts_core.adapters.parsers import parse_document
from hts_core.adapters.parsers.pdf_parser import extract_pdf_text


def encoded_pdf(lines, encoding="/WinAnsiEncoding", unicode_mapping=None):
    stream = b"BT /F1 12 Tf 72 800 Td "
    stream += b" 0 -16 Td ".join(b"(" + line + b") Tj" for line in lines) + b" ET"
    cmap = b""
    font_map = b""
    if unicode_mapping is not None:
        cmap = (b"/CIDInit /ProcSet findresource begin 12 dict begin begincmap "
                b"/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def "
                b"/CMapName /Fixture def /CMapType 2 def "
                b"1 begincodespacerange <00> <FF> endcodespacerange "
                b"1 beginbfchar <AD> <" + unicode_mapping.encode("ascii") + b"> endbfchar "
                b"endcmap CMapName currentdict /CMap defineresource pop end end")
        font_map = b" /ToUnicode 6 0 R"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding " + encoding.encode("ascii") + font_map + b" >>",
               b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"]
    if cmap:
        objects.append(b"<< /Length " + str(len(cmap)).encode("ascii") + b" >>\nstream\n" + cmap + b"\nendstream")
    result = b"%PDF-1.4\n"
    offsets = [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(result))
        result += f"{number} 0 obj\n".encode("ascii") + value + b"\nendobj\n"
    startxref = len(result)
    result += f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("ascii")
    result += b"".join(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets[1:])
    return result + f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode("ascii")


def test_winansi_code_173_survives_as_soft_hyphen_before_cleaning():
    data = encoded_pdf([b"O algo\xad", b"ritmo funciona."])
    assert extract_pdf_text(data) == "O algo\u00ad\nritmo funciona."
    assert parse_document("type1.pdf", data) == "O algoritmo funciona."


def test_winansi_soft_hyphen_inside_word_is_not_a_space():
    data = encoded_pdf([b"A infor\xadmacao chegou."])
    assert parse_document("type1.pdf", data) == "A informacao chegou."


@pytest.mark.parametrize("glyph, expected_raw, expected_clean", [
    ("space", "O guarda\nchuva chegou.", "O guarda chuva chegou."),
    ("hyphen", "O guarda-\nchuva chegou.", "O guarda-chuva chegou."),
    ("X", "O guardaX\nchuva chegou.", "O guardaX chuva chegou."),
])
def test_explicit_font_differences_override_default_code_173(glyph, expected_raw, expected_clean):
    encoding = f"<< /BaseEncoding /WinAnsiEncoding /Differences [173 /{glyph}] >>"
    data = encoded_pdf([b"O guarda\xad", b"chuva chegou."], encoding)
    assert extract_pdf_text(data) == expected_raw
    assert parse_document("custom.pdf", data) == expected_clean


def test_differences_for_another_character_do_not_hide_soft_hyphen():
    encoding = "<< /BaseEncoding /WinAnsiEncoding /Differences [65 /Z] >>"
    data = encoded_pdf([b"A algo\xad", b"ritmo."], encoding)
    assert extract_pdf_text(data) == "Z algo\u00ad\nritmo."


@pytest.mark.parametrize("mapping, expected", [("0058", "O algoX\nritmo."), ("0020", "O algo\nritmo."),
                                               ("00AD", "O algo\u00ad\nritmo.")])
def test_explicit_to_unicode_is_authoritative(mapping, expected):
    assert extract_pdf_text(encoded_pdf([b"O algo\xad", b"ritmo."], unicode_mapping=mapping)) == expected


def test_standard_encoding_with_custom_glyph_is_not_winansi():
    encoding = "<< /BaseEncoding /StandardEncoding /Differences [173 /X] >>"
    assert extract_pdf_text(encoded_pdf([b"a\xadb"], encoding)) == "aXb"


def test_real_spaces_and_hard_hyphens_are_not_soft_hyphens():
    data = encoded_pdf([b"O algo ", b"ritmo. O guarda-", b"chuva chegou."])
    assert parse_document("space.pdf", data) == "O algo ritmo. O guarda-chuva chegou."


def test_resource_maps_are_isolated_across_documents_and_threads():
    original = dict(EncodingDB.get_encoding("WinAnsiEncoding"))
    fixtures = [encoded_pdf([b"a\xadb"]),
                encoded_pdf([b"a\xadb"], "<< /BaseEncoding /WinAnsiEncoding /Differences [173 /space] >>")]
    with ThreadPoolExecutor(max_workers=4) as executor:
        result = list(executor.map(extract_pdf_text, fixtures * 8))
    assert result == ["a\u00adb", "a b"] * 8
    assert EncodingDB.get_encoding("WinAnsiEncoding") == original
