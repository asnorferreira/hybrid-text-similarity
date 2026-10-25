import re
from functools import lru_cache

import mwparserfromhell

from hts_core.adapters.refcorpus import wikitext_to_text
from hts_core.domain.text import clean_extracted, split_sentences


POLICY = 'raw_templates_segment_v1'
MARKER = 'HTSUNSUPPORTEDTEMPLATE'


@lru_cache(maxsize=64)
def curated_text(raw):
    changes = []
    start = raw.find('{{Info/País')
    end = raw.find("'''Nova Zelândia'''")
    if start >= 0 and end > start and raw[:end].rstrip().endswith('}}'):
        changes.append({'operation': 'bounded_country_infobox', 'before': raw[start:end], 'after': ''})
        raw = raw[:start] + raw[end:]
    code = mwparserfromhell.parse(raw)
    for tag in list(code.filter_tags(recursive=True)):
        if str(tag.tag).strip().lower() == 'sup' and str(tag.contents).strip() == '[[AO 1990]]':
            changes.append({'operation': 'orthographic_annotation_not_prose', 'before': str(tag), 'after': ''})
            code.remove(tag)
            continue
        if str(tag.tag).strip().lower() in {'ref', 'gallery', 'math', 'table', 'timeline', 'score'}:
            try:
                code.remove(tag)
            except ValueError:
                pass
    for template in reversed(code.filter_templates(recursive=True)):
        name = str(template.name).strip().casefold().replace('_', ' ')
        get = lambda key: str(template.get(key).value).strip() if template.has(key) else ''
        replacement = None
        if name in {'séc', 'século', 'sec'} and re.fullmatch(r'[IVXLCDM]+', get(1)):
            replacement = 'século ' + get(1)
        elif name in {'fmtn', 'formatnum'} and re.fullmatch(r'-?\d+(?:[.,]\d+)?', get(1)):
            replacement = get(1) + (' ' + get(2) if get(2) else '')
        elif name.startswith('formatnum:'):
            value = str(template.name).strip().split(':', 1)[1]
            if re.fullmatch(r'\d+(?:[.,]\d+)?(?: km2)?', value):
                replacement = value
        elif name in {'pepb', 'pbpe'} and get(1) and get(2):
            replacement = get(2 if name == 'pepb' else 1)
        elif name == 'langx' and get(2):
            replacement = get(2) + (' (' + get(4) + ')' if get(4) else '')
        elif name == 'lang' and get(2):
            replacement = get(2)
        elif name.startswith('lang-') and get(1):
            replacement = get(1)
        elif name == 'ipa-tudo' and get(1):
            replacement = get(1)
        elif name in {'-fim', 'imagem múltipla', 'gêneros de música popular do brasil', 'história da arquitetura', 'gótico'}:
            replacement = ''
        elif name.startswith(('info/', 'coord', 'citar ', 'referências', 'referencias', 'commons', 'portal', 'controle de autoridade', 'esboço', 'mais ', 'ver ', 'artigo principal', 'nota', 'carece', 'sem ', 'aviso', 'naveg', 'wik', '!')):
            replacement = ''
        if replacement is None:
            replacement = ' ' + MARKER + ' '
        try:
            before = str(template)
            code.replace(template, replacement)
            changes.append({'operation': 'template', 'before': before, 'after': replacement})
        except ValueError:
            pass
    extracted = clean_extracted(wikitext_to_text(str(code)))
    accepted, excluded = [], []
    for sentence in split_sentences(extracted):
        if any(token in sentence for token in (MARKER, '{{', '}}', '|nome_', '|imagem_', '|população_', '{|', '|}')):
            excluded.append({'text': sentence, 'reason': 'unsupported_or_residual_syntax_no_inference'})
        else:
            accepted.append(sentence)
    return ' '.join(accepted), {'policy': POLICY, 'operations': changes, 'excluded_sentences': excluded}


def extract_for_config(raw, config):
    return curated_text(raw)[0] if config.get('curation_policy') == POLICY else wikitext_to_text(raw)
