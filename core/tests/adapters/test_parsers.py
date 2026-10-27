import io
from pathlib import Path

import docx
import pytest
import reportlab
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pdfencrypt import StandardEncryption

from hts_core.adapters.parsers import UnsupportedFileError, parse_document, sniff_type
from hts_core.adapters.parsers.pdf_parser import NoTextLayerError, PdfReadError, ProtectedPdfError


def _pdf(lines: list[str]) -> bytes:
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    for line in lines:
        page.drawString(72, y, line)
        y -= 16
    page.save()
    return buffer.getvalue()


def _pdf_without_text() -> bytes:
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    page.rect(72, 600, 200, 100, fill=1)
    page.save()
    return buffer.getvalue()


def _docx(paragraphs: list[str]) -> bytes:
    document = docx.Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_pdf_line_break_hard_hyphen_is_joined():
    data = _pdf(["A deteccao de pla-", "gio usa o Rio-", "Grande. Outra frase."])
    assert parse_document("artigo.pdf", data) == "A deteccao de plagio usa o Rio-Grande. Outra frase."


def test_pdf_soft_hyphen_written_as_space_is_joined():
    data = _pdf(["gio usa o algo­", "ritmo de Smith."])
    assert "algoritmo" in parse_document("artigo.pdf", data)


def test_pdf_without_text_layer_is_refused():
    with pytest.raises(NoTextLayerError, match="sem camada de texto"):
        parse_document("escaneado.pdf", _pdf_without_text())


def test_pdf_with_unicode_soft_hyphen_is_joined():
    font = Path(reportlab.__file__).parent / "fonts" / "Vera.ttf"
    pdfmetrics.registerFont(TTFont("AuditVera", str(font)))
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    page.setFont("AuditVera", 12)
    page.drawString(72, 800, "O algo\u00ad")
    page.drawString(72, 784, "ritmo funciona.")
    page.save()
    from hts_core.adapters.parsers.pdf_parser import extract_pdf_text
    raw = extract_pdf_text(buffer.getvalue())
    assert "\u00ad" in raw
    assert parse_document("unicode.pdf", buffer.getvalue()) == "O algoritmo funciona."


def test_image_only_pdf_reports_possible_scan_without_claiming_ocr():
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer)
    page.drawImage(ImageReader(Image.new("RGB", (30, 30), "black")), 72, 600)
    page.save()
    with pytest.raises(NoTextLayerError, match="possível escaneamento.*OCR fora do escopo"):
        parse_document("imagem.pdf", buffer.getvalue())


def test_blank_pdf_is_distinguished_from_image_only_pdf():
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer)
    page.showPage()
    page.save()
    with pytest.raises(NoTextLayerError, match="vazio ou sem texto utilizável"):
        parse_document("vazio.pdf", buffer.getvalue())


def test_password_protected_pdf_has_explicit_error():
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer, encrypt=StandardEncryption("private-fixture-password"))
    page.drawString(72, 800, "Texto protegido")
    page.save()
    with pytest.raises(ProtectedPdfError, match="PDF protegido"):
        parse_document("protegido.pdf", buffer.getvalue())


def test_corrupt_pdf_has_explicit_read_error():
    with pytest.raises(PdfReadError, match="Falha de leitura"):
        parse_document("corrompido.pdf", b"%PDF-1.7\ntruncated")


def test_docx_soft_hyphen_removed_and_paragraphs_kept():
    data = _docx(["A infor­mação chegou.", "Segundo parágrafo."])
    assert parse_document("trabalho.docx", data) == "A informação chegou.\n\nSegundo parágrafo."


def test_txt_utf8_and_cp1252_with_broken_word():
    raw = "O texto tem uma pala-\nvra quebrada e acentuação."
    assert parse_document("a.txt", raw.encode("utf-8")) == "O texto tem uma palavra quebrada e acentuação."
    assert parse_document("b.txt", raw.encode("cp1252")) == "O texto tem uma palavra quebrada e acentuação."


def test_type_comes_from_content_not_extension():
    assert sniff_type(_pdf(["x"])) == "pdf"
    assert sniff_type(_docx(["x"])) == "docx"
    with pytest.raises(UnsupportedFileError, match="não confere"):
        parse_document("falso.txt", _pdf(["conteudo"]))
    with pytest.raises(UnsupportedFileError):
        parse_document("imagem.png", b"\x89PNG\r\n\x1a\n\x00\x00binario")


@pytest.mark.parametrize('failure', [None, 'text', 'images'])
def test_pdf_closes_each_page_before_advancing_and_on_extraction_error(monkeypatch, failure):
    from types import SimpleNamespace
    from hts_core.adapters.parsers import pdf_parser
    pages = []
    class Page:
        closed = False
        def __init__(self, number):
            self.number = number
        def extract_text(self):
            assert all(p.closed for p in pages[:self.number])
            if self.number == 1 and failure == 'text':
                raise ValueError('controlled extraction failure')
            return f'Página {self.number}'
        @property
        def images(self):
            if self.number == 1 and failure == 'images':
                raise ValueError('controlled image failure')
            return []
        def close(self):
            self.closed = True
    class Pdf:
        doc = SimpleNamespace(is_extractable=True)
        def __enter__(self):
            self.pages = pages
            return self
        def __exit__(self, *args):
            pass
    pages.extend(Page(i) for i in range(3))
    monkeypatch.setattr(pdf_parser.pdfplumber, 'open', lambda *args: Pdf())
    if failure:
        with pytest.raises(PdfReadError):
            pdf_parser.extract_pdf_text(b'fixture')
        assert pages[0].closed and pages[1].closed and not pages[2].closed
    else:
        assert pdf_parser.extract_pdf_text(b'fixture') == 'Página 0\nPágina 1\nPágina 2'
        assert all(page.closed for page in pages)
