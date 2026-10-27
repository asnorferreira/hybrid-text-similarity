import io

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect, PDFTextExtractionNotAllowed
from pdfminer.pdfexceptions import PDFException
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdffont import PDFSimpleFont
from pdfminer.pdftypes import list_value, resolve1
from pdfminer.psparser import PSLiteral, literal_name
from pdfplumber.utils.exceptions import PdfminerException


class NoTextLayerError(ValueError):
    pass


class ProtectedPdfError(ValueError):
    pass


class PdfReadError(ValueError):
    pass


def _default_winansi_soft_hyphen(spec) -> bool:
    if literal_name(spec.get("Subtype")) != "Type1" or "ToUnicode" in spec:
        return False
    encoding = resolve1(spec.get("Encoding"))
    if isinstance(encoding, dict):
        code = 0
        for item in list_value(resolve1(encoding.get("Differences", []))):
            if isinstance(item, int):
                code = item
            else:
                if code == 173:
                    return False
                code += 1
        encoding = resolve1(encoding.get("BaseEncoding"))
    return isinstance(encoding, PSLiteral) and literal_name(encoding) == "WinAnsiEncoding"


class _TextResourceManager(PDFResourceManager):
    def get_font(self, objid, spec):
        font = super().get_font(objid, spec)
        if isinstance(font, PDFSimpleFont) and _default_winansi_soft_hyphen(spec) and font.cid2unicode.get(173) == " ":
            # PDF 32000-1:2008, D.2 nota 5: WinAnsi 255 octal é hífen suave.
            font.cid2unicode = {**font.cid2unicode, 173: "\u00ad"}
        return font


def extract_pdf_text(data: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pdf.rsrcmgr = _TextResourceManager()
            if not pdf.doc.is_extractable:
                raise PDFTextExtractionNotAllowed("extração não permitida")
            pages = []
            has_images = False
            for page in pdf.pages:
                try:
                    pages.append(page.extract_text() or "")
                    has_images = has_images or bool(page.images)
                finally:
                    page.close()
    except (PDFPasswordIncorrect, PDFTextExtractionNotAllowed) as exc:
        raise ProtectedPdfError("PDF protegido; forneça uma versão com extração permitida") from exc
    except PdfminerException as exc:
        original = exc.args[0] if exc.args else None
        if isinstance(original, (PDFPasswordIncorrect, PDFTextExtractionNotAllowed)):
            raise ProtectedPdfError("PDF protegido; forneça uma versão com extração permitida") from exc
        raise PdfReadError("Falha de leitura do PDF") from exc
    except (PDFException, OSError, ValueError) as exc:
        raise PdfReadError("Falha de leitura do PDF") from exc
    text = "\n".join(pages)
    if not text.strip():
        reason = "com imagens, possível escaneamento" if has_images else "vazio ou sem texto utilizável"
        raise NoTextLayerError(f"PDF sem camada de texto utilizável: {reason} (OCR fora do escopo)")
    return text
