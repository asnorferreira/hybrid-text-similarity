import io

import docx
from lxml.etree import XMLSyntaxError


class DocxReadError(ValueError):
    pass


def extract_docx_text(data: bytes) -> str:
    try:
        document = docx.Document(io.BytesIO(data))
    except XMLSyntaxError as exc:
        raise DocxReadError('DOCX contém XML inválido') from exc
    return "\n\n".join(p.text for p in document.paragraphs)
