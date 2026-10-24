import io

import docx


def extract_docx_text(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    return "\n\n".join(p.text for p in document.paragraphs)
