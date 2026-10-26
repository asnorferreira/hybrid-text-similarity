import io
from pathlib import PurePosixPath
import zipfile

import docx
import lxml.etree as etree
from lxml.etree import XMLSyntaxError


class DocxReadError(ValueError):
    pass


def validate_package(data: bytes) -> None:
    limit = 20 * 1024 * 1024
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(entries) > 2048 or len(set(names)) != len(names) or sum(entry.file_size for entry in entries) > limit:
            raise DocxReadError('estrutura ou expansão do DOCX excede o limite')
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if not path.parts or path.is_absolute() or '..' in path.parts or '\\' in entry.filename or ':' in path.parts[0] or entry.flag_bits & 1:
                raise DocxReadError('estrutura interna do DOCX inválida')
            if entry.filename.endswith(('.xml', '.rels')):
                with archive.open(entry) as stream:
                    content = stream.read(limit + 1)
                if len(content) > limit:
                    raise DocxReadError('expansão do DOCX excede o limite')
                parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
                tree = etree.fromstring(content, parser).getroottree()
                if tree.docinfo.doctype:
                    raise DocxReadError('DTD não permitido em DOCX')


def extract_docx_text(data: bytes) -> str:
    try:
        validate_package(data)
        document = docx.Document(io.BytesIO(data))
    except (XMLSyntaxError, zipfile.BadZipFile, RuntimeError) as exc:
        raise DocxReadError('DOCX contém XML ou estrutura inválida') from exc
    return "\n\n".join(p.text for p in document.paragraphs)
