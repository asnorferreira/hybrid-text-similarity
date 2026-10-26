from collections import defaultdict
from datetime import datetime, timezone
import io
from pathlib import Path
from xml.sax.saxutils import escape
import zipfile

import docx
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate

from hts_core.adapters.dataset_store import digest, read_jsonl, seal, verify_seal, write_json, write_jsonl, write_new
from hts_core.adapters.parsers import parse_document


def font_glyphs(font):
    glyphs = font.face.charToGlyph
    if glyphs is None:
        raise ValueError('font glyph map is unavailable')
    return glyphs


def render(text, kind):
    if kind == 'txt':
        return text.encode('utf-8'), {'encoding': 'UTF-8 without BOM', 'newline': 'LF'}
    stream = io.BytesIO()
    if kind == 'docx':
        document = docx.Document()
        document.add_paragraph(text)
        props = document.core_properties
        props.author = props.last_modified_by = ''
        props.created = props.modified = datetime(2000, 1, 1, tzinfo=timezone.utc)
        document.save(stream)
        output = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as source, zipfile.ZipFile(output, 'w', zipfile.ZIP_STORED) as archive:
            for name in sorted(source.namelist()):
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o600 << 16
                archive.writestr(entry, source.read(name))
        return output.getvalue(), {'zip_datetime': '1980-01-01', 'core_datetime': '2000-01-01', 'metadata': 'no class/source in rendered content'}
    if kind != 'pdf':
        raise ValueError('formato não suportado')
    font_path = Path(__file__).resolve().parents[3]/'assets/fonts/NotoSans-Regular.ttf'
    expected_font = 'b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5'
    if digest(font_path.read_bytes()) != expected_font:
        raise ValueError('hash da fonte Unicode divergente')
    font = TTFont('HTSDatasetNotoSans', str(font_path))
    missing = sorted({ord(c) for c in text if not c.isspace() and ord(c) not in font_glyphs(font)})
    fallback = None
    arabic = None
    if missing:
        fallback_path = font_path.with_name('NotoSansCJKsc-Regular-HTS.ttf')
        if digest(fallback_path.read_bytes()) != '568d44ed35df4ffdd53ce99dab039b2c0b60c291847574e9b46f50415c47ce7b':
            raise ValueError('hash da fonte CJK divergente')
        fallback = TTFont('HTSDatasetNotoCJK', str(fallback_path))
        missing = [c for c in missing if c not in font_glyphs(fallback)]
        if missing:
            arabic_path = font_path.with_name('IBMPlexSansArabic-Regular.ttf')
            if digest(arabic_path.read_bytes()) != '6f611412270a132bbac838da9259d4c68569b4175f3b3b8fa3fa36a30b56dab9':
                raise ValueError('hash da fonte árabe divergente')
            arabic = TTFont('HTSDatasetNotoArabic', str(arabic_path))
            missing = [c for c in missing if c not in font_glyphs(arabic)]
            if missing:
                raise ValueError('fontes PDF não cobrem todos os caracteres: ' + ','.join(f'U+{c:04X}' for c in missing))
            pdfmetrics.registerFont(arabic)
        pdfmetrics.registerFont(fallback)
    pdfmetrics.registerFont(font)
    document = SimpleDocTemplate(stream, invariant=1, title='', author='', subject='', creator='hts format writer',
                                 leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    style = ParagraphStyle('content', fontName='HTSDatasetNotoSans', fontSize=11, leading=15)
    if fallback:
        from itertools import groupby
        parts = []
        def font_for(char):
            if char.isspace() or ord(char) in font_glyphs(font):
                return None
            return 'HTSDatasetNotoCJK' if ord(char) in font_glyphs(fallback) else 'HTSDatasetNotoArabic'
        for font_name, chars in groupby(text, key=font_for):
            part = escape(''.join(chars))
            parts.append('<font name="' + font_name + '">' + part + '</font>' if font_name else part)
        content = ''.join(parts)
    else:
        content = escape(text)
    document.build([Paragraph(content, style)])
    return stream.getvalue(), {'font': 'Noto Sans Regular; upstream OFL-1.1 preserved in assets/fonts/OFL.txt', 'font_sha256': digest(font_path.read_bytes()),
                               'fallback': 'NotoSansCJKsc-Regular-HTS, OFL-CJK.txt; static wght=400; manifest-cjk-static.json' if fallback else None,
                               'fallback_sha256': '568d44ed35df4ffdd53ce99dab039b2c0b60c291847574e9b46f50415c47ce7b' if fallback else None,
                               'arabic_font_sha256': '6f611412270a132bbac838da9259d4c68569b4175f3b3b8fa3fa36a30b56dab9' if arabic else None,
                               'arabic_font': 'IBM Plex Sans Arabic Regular; OFL-PlexArabic.txt; manifest-plex-arabic.json' if arabic else None,
                               'arabic_presentation': 'Unicode glyphs; contextual shaping/bidi not implemented' if arabic else None,
                               'invariant': True, 'identity': 'container bytes and canonical content distinct'}


def add_formats(folder, destination, limit=None):
    from hts_core.adapters.dataset_validation import validate_data
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    if manifest['metadata']['purpose'].startswith('frozen'):
        raise PermissionError('versão congelada não aceita novos formatos; reconstruir candidato em destino novo')
    if manifest['metadata']['purpose'] not in {'pilot', 'experimental_candidate', 'operational_derivation'}:
        raise PermissionError('formatos exigem versão candidata ou piloto')
    if (folder/'formats.jsonl').exists():
        raise ValueError('formatos existentes são imutáveis; usar a versão anterior aos formatos')
    validate_data(folder)
    destination.mkdir(parents=True, exist_ok=False)
    for name in manifest['files']:
        if name != 'validation.json':
            write_new(destination/name, (folder/name).read_bytes())
    grouped = defaultdict(list)
    for pair in read_jsonl(folder/'pairs.jsonl'):
        grouped[pair['content_id']].append(pair)
    entries, failures = [], []
    chosen = []
    strata = sorted({(p['synthetic_type'], p['method']) for rows in grouped.values() for p in rows})
    for kind, method in strata:
        candidates = sorted(cid for cid, rows in grouped.items() if any(p['synthetic_type'] == kind and p['method'] == method for p in rows))
        if candidates and candidates[0] not in chosen:
            chosen.append(candidates[0])
    chosen += [cid for cid in sorted(grouped) if cid not in chosen]
    config = __import__('json').loads((folder/'config.json').read_bytes())
    if config['purpose'] == 'operational_derivation':
        from hts_core.adapters.dataset_operational import selected_format_contents
        if limit is not None:
            raise ValueError('cobertura operacional vem da especificação; não truncar com limit')
        chosen = selected_format_contents([p for rows in grouped.values() for p in rows])
    for cid in chosen[:limit]:
        pairs = grouped[cid]
        pair = pairs[0]
        for kind in ('txt', 'docx', 'pdf'):
            filename = f'formats/{cid}.{kind}'
            try:
                data, metadata = render(pair['text'], kind)
            except ValueError as exc:
                failures.append({'content_id': cid, 'kind': kind, 'stage': 'render', 'error': str(exc)})
                continue
            write_new(destination/filename, data)
            try:
                extracted = parse_document(filename, data)
            except ValueError as exc:
                failures.append({'content_id': cid, 'kind': kind, 'stage': 'parse', 'error': type(exc).__name__})
                extracted = ''
            entry = {'content_id': cid, 'family_ids': sorted(p['id'] for p in pairs), 'split': pair['split'], 'kind': kind,
                     'file': filename, 'sha256': digest(data), 'extracted': extracted, 'expected': pair['text'],
                     'roundtrip': extracted == pair['text'], 'container': metadata}
            entries.append(entry)
            if not entry['roundtrip']:
                failures.append({'content_id': cid, 'kind': kind, 'stage': 'roundtrip', 'expected': pair['text'], 'actual': extracted})
    write_jsonl(destination/'formats.jsonl', entries)
    write_json(destination/'format-failures.json', failures)
    write_json(destination/'validation.json', {'status': 'format_failures_preserved'} if failures else validate_data(destination, sealed=False))
    result = seal(destination, {**manifest['metadata'], 'parent_version': manifest['version'], 'formats_limit': limit})
    if failures:
        raise ValueError(f'{len(failures)} falhas preservadas em format-failures.json; versão não validada')
    return result
