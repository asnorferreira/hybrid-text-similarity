import io
import re
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
        except zipfile.BadZipFile as exc:
            raise ValueError('arquivo ZIP/DOCX corrompido') from exc
        raise UnsupportedFileError("arquivo zip que não é DOCX")
    if b"\x00" in data[:4096]:
        raise UnsupportedFileError("arquivo binário não suportado")
    return "txt"


_EXTRACTORS = {"pdf": extract_pdf_text, "docx": extract_docx_text, "txt": extract_txt_text}


def parse_document(filename: str, data: bytes, *, diagnostics=None) -> str:
    """Tipo pelo conteúdo, não pela extensão; a extensão só precisa concordar."""
    kind = sniff_type(data)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension and extension != kind:
        raise UnsupportedFileError(f"extensão .{extension} não confere com o conteúdo ({kind})")
    raw = _EXTRACTORS[kind](data)
    cleaned = clean_extracted(raw)
    if diagnostics is not None:
        diagnostics.update(format=kind, cleanup_changed=raw != cleaned, soft_hyphen_observed='\u00ad' in raw,
                           hyphen_linebreak_observed=bool(re.search(r'-[ \t]*\n', raw)))
    return cleaned
