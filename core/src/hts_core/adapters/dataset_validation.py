from collections import Counter, defaultdict
from pathlib import Path

from hts_core.adapters.dataset_schemas import Format, Pair, Source
from hts_core.adapters.dataset_store import digest, identity, inside, read_json, read_jsonl, verify_seal
from hts_core.domain.text import clean_extracted, split_sentences, word_count
from hts_core.domain.preprocess import semantic_text


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_data(folder, sealed=True):
    folder = Path(folder)
    if sealed:
        verify_seal(folder)
    config = read_json(folder/'config.json')
    sources = [Source.model_validate(s).model_dump() for s in read_jsonl(folder/'sources.jsonl')]
    pairs = [Pair.model_validate(p).model_dump() for p in read_jsonl(folder/'pairs.jsonl')] if (folder/'pairs.jsonl').exists() else []
    _require(sources and (pairs or config['purpose'] == 'source_preparation'), 'dataset vazio')
    _require(len({s['id'] for s in sources}) == len(sources), 'IDs de fonte duplicados')
    _require(len({p['id'] for p in pairs}) == len(pairs), 'IDs de par duplicados')
    by_id = {s['id']: s for s in sources}
    origins, group_splits, page_splits, content_splits = {}, defaultdict(set), defaultdict(set), defaultdict(set)
    distribution = Counter()
    for source in sources:
        group_splits[source['group']].add(source['split'])
        page_splits[(source['provider'], source['pageid'])].add(source['split'])
        for layer in ('raw', 'extracted', 'normalized'):
            _require(digest(inside(folder, source[f'{layer}_file']).read_bytes()) == source[f'{layer}_sha256'], 'hash de fonte divergente')
        _require(inside(folder, source['normalized_file']).read_text(encoding='utf-8') == source['text'], 'texto normalizado divergente')
        from hts_core.adapters.refcorpus import wikitext_to_text
        extracted = wikitext_to_text(inside(folder, source['raw_file']).read_text(encoding='utf-8'))
        _require(extracted.encode() == inside(folder, source['extracted_file']).read_bytes(), 'conversão raw/extracted divergente')
        _require(clean_extracted(extracted) == source['text'], 'normalização não corresponde à extração')
        _require(clean_extracted(source['text']) == source['text'], 'fonte não normalizada')
        eligible = [(i, text) for i, text in enumerate(split_sentences(source['text']))
                    if len(text.split()) >= config['minimum_sentence_words']][:config['segment_sentences']]
        _require([r['text'] for r in source['sentences']] == [text for _, text in eligible], 'segmento selecionado divergente da política')
        _require([r['parameters']['original_sentence_position'] for r in source['sentences']] == [i for i, _ in eligible], 'posições originais divergentes')
        distribution['source:' + source['split'] + ':' + source['theme']] += 1
        for row in source['sentences']:
            _require(row['id'] not in origins, 'ID de sentença duplicado')
            origins[row['id']] = (source['id'], row)
        _check_rows(source['sentences'], ' '.join(row['text'] for row in source['sentences']))
    _require(all(len(v) == 1 for v in group_splits.values()), 'grupo em splits diferentes')
    _require(all(len(v) == 1 for v in page_splits.values()), 'mesma página em treino/teste')
    from hts_core.domain.dataset import source_groups, split_groups
    expected_groups, near_alerts = source_groups(sources, config['near_duplicate_threshold'], config['shingle_size'])
    _require(all(s['group'] == expected_groups[s['id']] for s in sources), 'família/quase duplicata não agrupada')
    expected_split = split_groups(expected_groups, config['seed'], tuple(config['split_percent']))
    _require(all(s['split'] == expected_split[s['id']] for s in sources), 'split difere da alocação por grupos/seed')
    for pair in pairs:
        _require(pair['source_id'] in by_id, 'fonte focal órfã')
        _require(pair['content_id'] == identity({'text': pair['text']}), 'identidade de conteúdo divergente')
        _require(pair['source_id'] in pair['source_ids'], 'fonte focal ausente')
        _require(len(pair['source_ids']) == len(set(pair['source_ids'])), 'fontes repetidas no par')
        _require(all(s in by_id for s in pair['source_ids']), 'fonte órfã')
        _require(all(by_id[s]['split'] == pair['split'] for s in pair['source_ids']), 'fonte do par/patchwork externa ao split')
        _check_rows(pair['sentences'], pair['text'])
        ancestors_union, numerator = set(), 0
        for row in pair['sentences']:
            _require(row['semantic_target'] is None and row['validated_class'] is None, 'gabarito semântico fabricado')
            ancestry = {(a['source_id'], a['sentence_id']) for a in row['ancestors']}
            _require(ancestry and len(ancestry) == len(row['ancestors']), 'proveniência ausente/duplicada')
            for sid, sentid in ancestry:
                _require(sentid in origins and origins[sentid][0] == sid, 'sentença ancestral órfã')
            ancestors_union.update(sid for sid, _ in ancestry)
            numerator += int(any(sid == pair['source_id'] for sid, _ in ancestry))
        _require(set(pair['source_ids']) == ancestors_union | {pair['source_id']}, 'conjunto de fontes divergente')
        _require(pair['r'] == {'numerator': numerator, 'denominator': len(pair['sentences'])}, 'r/denominador incorreto')
        expected_r = {sid: {'numerator': sum(any(a['source_id'] == sid for a in row['ancestors']) for row in pair['sentences']),
                           'denominator': len(pair['sentences'])} for sid in pair['source_ids']}
        _require(pair['r_by_source'] == expected_r, 'r por fonte incorreto')
        _check_transformation(pair, by_id, origins)
        if pair['synthetic_type'] in {'C5', 'C6'}:
            from hts_core.adapters.dataset_llm import validate_cached
            record = read_json(inside(folder, 'cache/' + pair['generation']['cache_request_id'] + '.json'))
            output = validate_cached(record, record['request'])
            _require(record['cache_key'] == pair['generation']['cache_key'], 'cache divergente no candidato')
            _require(clean_extracted(' '.join(row['text'] for row in output)) == pair['text'], 'conteúdo divergente do cache')
        content_splits[pair['content_id']].add(pair['split'])
        distribution['pair:' + ':'.join((pair['split'], pair['synthetic_type'], pair['method'], pair['severity']))] += 1
    _require(all(len(v) == 1 for v in content_splits.values()), 'conteúdo derivado atravessa splits')
    format_path = folder/'formats.jsonl'
    formats = read_jsonl(format_path) if format_path.exists() else []
    by_content = {p['content_id']: p for p in pairs}
    for entry in formats:
        entry = Format.model_validate(entry).model_dump()
        _require(entry['content_id'] in by_content, 'formato órfão')
        expected = by_content[entry['content_id']]
        _require(entry['split'] == expected['split'], 'variante de formato em outro split')
        _require(set(entry['family_ids']) == {p['id'] for p in pairs if p['content_id'] == entry['content_id']}, 'família de formato divergente')
        data = inside(folder, entry['file']).read_bytes()
        _require(digest(data) == entry['sha256'], 'hash de formato divergente')
        from hts_core.adapters.parsers import parse_document
        actual = parse_document(entry['file'], data)
        _require(entry['expected'] == expected['text'], 'oráculo de formato alterado')
        _require(entry['extracted'] == actual, 'extração de formato divergente')
        _require(entry['roundtrip'] == (actual == expected['text']) and entry['roundtrip'], 'round-trip divergente')
        distribution['format:' + entry['split'] + ':' + entry['kind']] += 1
    common = defaultdict(list)
    for source in sources:
        for row in source['sentences']:
            common[row['semantic']].append(source['id'])
    shared = [{'sentence_sha256': digest(text.encode()), 'sources': sorted(set(ids))} for text, ids in common.items() if len(set(ids)) > 1]
    return {'status': 'structurally_valid', 'sources': len(sources), 'groups': len(group_splits), 'pairs': len(pairs),
            'sentences': sum(len(p['sentences']) for p in pairs), 'formats': len(formats),
            'distribution': dict(sorted(distribution.items())), 'near_duplicate_links': near_alerts,
            'shared_sentence_alerts': shared, 'human_review': 'pending', 'semantic_quality': 'not_certified',
            'limits': 'shingle detector and exact matches do not rule out all semantic overlap'}


def _check_rows(rows, text):
    _require([s['position'] for s in rows] == list(range(len(rows))), 'posições inconsistentes')
    _require(len({s['id'] for s in rows}) == len(rows), 'IDs de sentença repetidos')
    _require([s['text'] for s in rows] == split_sentences(clean_extracted(text)), 'resegmentação divergente')
    _require(all(s['words'] == word_count(s['text']) for s in rows), 'contagem de palavras divergente')
    _require(all(s['semantic'] == semantic_text(s['text']) for s in rows), 'perfil semântico divergente')


def _check_transformation(pair, sources, origins):
    kind, method = pair['synthetic_type'], pair['method']
    allowed = {'C0': {'negative_easy', 'negative_hard'}, 'C1': {'copy'}, 'C2': {'character_substitution'},
               'C3': {'insert'}, 'C4': {'patchwork'}, 'C5': {'llm_direct', 'backtranslation'},
               'C6': {'phrase_guided_rewrite'}, 'C7': {'reorder'}}
    _require(method in allowed[kind], 'classe/operação incompatíveis')
    rows = pair['sentences']
    if kind in {'C1', 'C2', 'C7'}:
        _require(all(a['source_id'] == pair['source_id'] for row in rows for a in row['ancestors']), 'derivação atribuída a outra fonte')
    if kind in {'C0', 'C1', 'C3', 'C4', 'C7'}:
        for row in rows:
            _require(len(row['ancestors']) == 1, 'cópia exige ancestral único')
            _require(row['text'] == origins[row['ancestors'][0]['sentence_id']][1]['text'], 'cópia/permutação adulterada')
    if kind == 'C0':
        _require(pair['r']['numerator'] == 0, 'negativo derivado da focal')
        donor = sources[pair['generation']['donor']]
        _require((donor['theme'] == sources[pair['source_id']]['theme']) == (method == 'negative_hard'), 'tema do negativo inválido')
    if kind == 'C1':
        _require(pair['text'] == ' '.join(r['text'] for r in sources[pair['source_id']]['sentences']), 'C1 não é igualdade contratada')
    if kind == 'C7':
        order = pair['generation']['permutation']
        original = sources[pair['source_id']]['sentences']
        _require(sorted(order) == list(range(len(original))) and order != list(range(len(original))), 'permutação inválida/sem efeito')
        _require([r['ancestors'][0]['sentence_id'] for r in rows] == [original[i]['id'] for i in order], 'permutação/proveniência divergentes')
    if kind == 'C2':
        infos = pair['generation']['by_sentence']
        _require(len(infos) == len(rows), 'edições/sentenças divergentes')
        for row, info in zip(rows, infos):
            _require(len(row['ancestors']) == 1 and row['ancestors'][0]['sentence_id'] == info['source_sentence_id'], 'edição/proveniência divergente')
            original = origins[info['source_sentence_id']][1]['text']
            output, seen = list(original), set()
            for op in info['operations']:
                pos = op['position']
                _require(0 <= pos < len(output) and pos not in seen, 'posição de edição inválida')
                _require(op['before'] == original[pos] and op['after'] != op['before'] and len(op['after']) == 1, 'edição sem efeito/incorreta')
                seen.add(pos)
                output[pos] = op['after']
            eligible = sum(c.isalpha() and c.islower() for c in original)
            _require(info['eligible'] == eligible and info['realized_count'] == len(seen), 'contagem de edição inválida')
            _require(info['realized_rate'] == (len(seen) / eligible if eligible else 0), 'taxa realizada inválida')
            _require(''.join(output) == row['text'], 'saída não corresponde às operações')
            _require(len(seen) == min(eligible, int(eligible * info['requested_rate'] + .5)), 'quantidade não corresponde à taxa solicitada')
    if kind == 'C3':
        info = pair['generation']
        _require(0 < pair['r']['numerator'] < len(rows), 'inserção não mistura origens')
        _require(info['total_count'] == len(rows) and info['focal_count'] == pair['r']['numerator'], 'composição C3 divergente')
    if kind == 'C4':
        _require(2 <= len({a['source_id'] for r in rows for a in r['ancestors']}) <= 4, 'patchwork exige 2–4 origens')
    if kind in {'C5', 'C6'}:
        _require('cache_key' in pair['generation'], 'transformação LLM sem cache identificado')


def evaluation_inputs(folder, split):
    if split == 'test':
        raise PermissionError('teste final fechado na S4; exige protocolo e autorização S5 próprios')
    if split not in {'train', 'validation'}:
        raise ValueError('split inválido')
    validate_data(folder)
    pairs = read_jsonl(Path(folder)/'pairs.jsonl')
    return [{'id': p['content_id'], 'text': p['text']} for p in pairs if p['split'] == split]


def validate_training_idf(folder, idf_folder):
    from hts_core.adapters import nlp
    from hts_core.application.text_pipeline import prepare_sentences
    validate_data(folder)
    sources = [s for s in read_jsonl(Path(folder)/'sources.jsonl') if s['split'] == 'train']
    table = read_json(Path(idf_folder)/'idf.json')
    descriptor = read_json(Path(idf_folder)/'construction.json')
    training = {s['id'] for s in sources}
    _require({s['id'] for s in descriptor['training_sources']} == training, 'dados de teste/validação no IDF')
    counts = Counter()
    for source in sources:
        unique = {t for row in prepare_sentences(source['text'], nlp.analyze, nlp.STOPWORDS) for t in row.lexical}
        for token in unique:
            counts[token] += 1
    _require(table['n_docs'] == len(sources) and table['df'] == dict(counts), 'df/N do IDF divergentes do treino')
    body = {k: v for k, v in table.items() if k != 'version'}
    _require(descriptor['table_content_sha256'] == identity(body), 'hash da tabela IDF divergente')
    descriptor_body = {k: v for k, v in descriptor.items() if k != 'identity'}
    _require(descriptor['identity'] == table['version'] == identity(descriptor_body), 'identidade de construção IDF divergente')
    return {'status': 'training_only_verified', 'sources': len(sources), 'terms': len(counts), 'version': table['version']}
