import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile


def pdf_bytes():
    stream=b'BT /F1 12 Tf 72 720 Td (O algo\\255ritmo funciona.) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
             b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
             b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    data=bytearray(b'%PDF-1.4\n')
    offsets=[0]
    for i, obj in enumerate(objects,1):
        offsets.append(len(data)); data.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(data)
    data.extend(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    data.extend(b''.join(f'{offset:010} 00000 n \n'.encode() for offset in offsets[1:]))
    data.extend(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return bytes(data)


def docx_bytes(malformed=False):
    parts={'[Content_Types].xml':'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
           '_rels/.rels':'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
           'word/document.xml':'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>A informação chegou.</w:t></w:r></w:p><w:p><w:r><w:t>O guarda-chuva chegou.</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'}
    if malformed:
        parts['word/document.xml'] = '<broken'
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_STORED) as archive:
        for name, text in sorted(parts.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.create_system=3
            info.external_attr=0o600<<16
            archive.writestr(info,text.encode('utf-8'))
    return stream.getvalue()


def generate(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    files={'tipo1-perda.pdf':pdf_bytes(),'texto.docx':docx_bytes(),'corrompido.docx':docx_bytes(malformed=True)}
    manifest={'development_only':True,'generator':'gerar_fixtures_ci.py v2; ZIP Unix explícito preserva bytes Linux históricos; XML inválido acrescentado',
              'source':['O algoritmo funciona.'],'suspect':['A informação chegou.','O guarda-chuva chegou.'],
              'sha256':{name:hashlib.sha256(data).hexdigest() for name,data in files.items()}}
    files['expected.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    for name,data in files.items():
        path=folder/name
        if path.exists() and path.read_bytes()!=data:
            raise ValueError(f'arquivo existente divergente: {name}; use diretório novo')
        path.write_bytes(data)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    print(json.dumps(generate(parser.parse_args().out),ensure_ascii=False))
