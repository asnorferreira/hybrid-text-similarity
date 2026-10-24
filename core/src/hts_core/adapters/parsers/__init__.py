import io
import zipfile

from hts_core.adapters.parsers.docx_parser import extract_docx_text
from hts_core.adapters.parsers.pdf_parser import extract_pdf_text
from hts_core.adapters.parsers.txt_parser import extract_txt_text
from hts_core.domain.text import clean_extracted


class UnsupportedFileError(ValueError):
    pass


def sniff_type(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if "word/document.xml" in archive.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            pass
        raise UnsupportedFileError("arquivo zip que não é DOCX")
    if b"\x00" in data[:4096]:
        raise UnsupportedFileError("arquivo binário não suportado")
    return "txt"


_EXTRACTORS = {"pdf": extract_pdf_text, "docx": extract_docx_text, "txt": extract_txt_text}


def parse_document(filename: str, data: bytes) -> str:
    """Tipo pelo conteúdo, não pela extensão; a extensão só precisa concordar."""
    kind = sniff_type(data)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension and extension != kind:
        raise UnsupportedFileError(f"extensão .{extension} não confere com o conteúdo ({kind})")
    return clean_extracted(_EXTRACTORS[kind](data))
