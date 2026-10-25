from collections import Counter, defaultdict
from pathlib import Path
from functools import lru_cache

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
        manifest = verify_seal(folder)
    config = read_json(folder/'config.json')
    _check_config(config)
    if sealed:
        expected_purpose = {'frozen_operational_derivation': 'operational_derivation', 'frozen_derivation_candidate': 'experimental_candidate'}.get(manifest['metadata']['purpose'], manifest['metadata']['purpose'])
        _require(config['purpose'] == expected_purpose, 'finalidade config/manifesto divergente')
        if 'config_identity' in manifest['metadata']:
            _require(manifest['metadata']['config_identity'] == identity(config), 'configuração/identidade divergentes')
    sources = [Source.model_validate(s).model_dump() for s in read_jsonl(folder/'sources.jsonl')]
    pairs = [Pair.model_validate(p).model_dump() for p in read_jsonl(folder/'pairs.jsonl')] if (folder/'pairs.jsonl').exists() else []
    _require(sources and (pairs or config['purpose'] == 'source_preparation'), 'dataset vazio')
    _require(len({s['id'] for s in sources}) == len(sources), 'IDs de fonte duplicados')
    _require(len({p['id'] for p in pairs}) == len(pairs), 'IDs de par duplicados')
    if config.get('record_contract') == 'assessment_v2':
        from hts_core.adapters.dataset_review import assessment_state
        frozen = sealed and manifest['metadata']['purpose'] == 'frozen_operational_derivation'
        review_states = read_json(folder/'review.json') if frozen else None
        originals = read_jsonl(folder/'construction-pairs.jsonl') if frozen else pairs
        _require(len(originals) == len(pairs), 'migração de estados perdeu pares')
        for pair, original in zip(pairs, originals):
            _require(pair['human_review'] == 'not_performed', 'revisão humana inexistente deve ser not_performed')
            _require(pair['content_assessment'] == assessment_state(pair['id'], review_states), 'avaliação individual diverge do registro vinculado')
            _require(all(r['validation'] == 'structural' for r in pair['sentences']), 'avaliação do par não aprova sentenças individualmente')
            _require({**pair, 'content_assessment': assessment_state(pair['id'])} == original, 'migração alterou conteúdo/operação ou estado candidato')
    by_id = {s['id']: s for s in sources}
    origins, group_splits, page_splits, content_splits = {}, defaultdict(set), defaultdict(set), defaultdict(set)
    distribution = Counter()
    for source in sources:
        from datetime import datetime
        datetime.fromisoformat(source['collected_utc'])
        _require(source['id'] == f"wikipedia-pt-{source['pageid']}-{source['revision']}", 'ID/revisão da fonte divergente')
        _require(len(source['sentences']) >= config['minimum_sentences'], 'fonte abaixo do mínimo de sentenças')
        group_splits[source['group']].add(source['split'])
        page_splits[(source['provider'], source['pageid'])].add(source['split'])
        for layer in ('raw', 'extracted', 'normalized'):
            _require(digest(inside(folder, source[f'{layer}_file']).read_bytes()) == source[f'{layer}_sha256'], 'hash de fonte divergente')
        _require(inside(folder, source['normalized_file']).read_text(encoding='utf-8') == source['text'], 'texto normalizado divergente')
        from hts_core.adapters.dataset_curation import extract_for_config
        if config.get('curation_policy'):
            from hts_core.adapters.dataset_curation import curated_text
            extracted, ledger = curated_text(inside(folder, source['raw_file']).read_text(encoding='utf-8'))
            _require(read_json(folder/f"sources/{source['id']}.curation.json") == ledger, 'registro de curadoria diverge do raw')
            _require(source['title'] not in config.get('source_exclusions', {}), 'fonte explicitamente excluída foi reincluída')
        else:
            extracted = extract_for_config(inside(folder, source['raw_file']).read_text(encoding='utf-8'), config)
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
            _require(not row['ancestors'] and row['transformation'] == 'source', 'fonte com ancestrais/transformação espúrios')
            origins[row['id']] = (source['id'], row)
        _check_rows(source['sentences'], ' '.join(row['text'] for row in source['sentences']), source['id'])
    _require(all(len(v) == 1 for v in group_splits.values()), 'grupo em splits diferentes')
    _require(all(len(v) == 1 for v in page_splits.values()), 'mesma página em treino/teste')
    from hts_core.domain.dataset import source_groups, split_groups
    expected_groups, near_alerts = source_groups(sources, config['near_duplicate_threshold'], config['shingle_size'])
    _require(all(s['group'] == expected_groups[s['id']] for s in sources), 'família/quase duplicata não agrupada')
    expected_split = split_groups(expected_groups, config['seed'], tuple(config['split_percent']))
    _require(all(s['split'] == expected_split[s['id']] for s in sources), 'split difere da alocação por grupos/seed')
    for pair in pairs:
        from hts_core.domain.dataset import stable_id
        _require(pair['seed'] == config['seed'], 'seed do par/config divergente')
        _require(pair['id'] == stable_id(pair['source_id'], pair['synthetic_type'], pair['method'], pair['severity'], str(pair['seed']), pair['content_id']), 'ID do par divergente')
        _require(pair['source_id'] in by_id, 'fonte focal órfã')
        _require(pair['content_id'] == identity({'text': pair['text']}), 'identidade de conteúdo divergente')
        _require(pair['source_id'] in pair['source_ids'], 'fonte focal ausente')
        _require(len(pair['source_ids']) == len(set(pair['source_ids'])), 'fontes repetidas no par')
        _require(all(s in by_id for s in pair['source_ids']), 'fonte órfã')
        _require(all(by_id[s]['split'] == pair['split'] for s in pair['source_ids']), 'fonte do par/patchwork externa ao split')
        _check_rows(pair['sentences'], pair['text'], pair['id'])
        ancestors_union, numerator = set(), 0
        for row in pair['sentences']:
            _require(row['semantic_target'] is None and row['validated_class'] is None, 'gabarito semântico fabricado')
            _require(row['transformation'] == pair['method'] and row['parameters'] == pair['generation'], 'metadados de sentença/par divergentes')
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
        _check_transformation(pair, by_id, origins, config)
        if pair['synthetic_type'] in {'C5', 'C6'}:
            from hts_core.adapters.dataset_llm import validate_lineage
            record = read_json(inside(folder, 'cache/' + pair['generation']['cache_request_id'] + '.json'))
            records = {}
            for path in sorted((folder/'cache').glob('*.json')):
                cached = read_json(path)
                _require(path.stem == cached['request_id'], 'nome/ID do cache divergente')
                _require(cached['cache_key'] not in records, 'chaves de cache duplicadas')
                records[cached['cache_key']] = cached
            validate_lineage(record, records, by_id, pair)
            if config['purpose'] == 'operational_derivation':
                _require(record['request']['provider'] == 'Codex-session', 'interface não prevista na especificação operacional')
                _require(all(r['intended_class'] is None for r in pair['sentences']), 'C5/C6 operacional sem classe semântica automática')
        content_splits[pair['content_id']].add(pair['split'])
        distribution['pair:' + ':'.join((pair['split'], pair['synthetic_type'], pair['method'], pair['severity']))] += 1
    _require(all(len(v) == 1 for v in content_splits.values()), 'conteúdo derivado atravessa splits')
    if (folder/'content-exclusions.json').exists():
        from hts_core.adapters.dataset_operational import excluded_pair_from_cache, validate_content_exclusion
        exclusions = read_json(folder/'content-exclusions.json')
        _require(config.get('content_exclusion_policy') == 'documented_automated_assessment_exclusions_v1', 'política de exclusão ausente')
        _require(len({e['request_id'] for e in exclusions}) == len(exclusions), 'exclusões duplicadas')
        cache = [read_json(path) for path in sorted((folder/'cache').glob('*.json'))]
        records_by_key = {r['cache_key']: r for r in cache}
        records_by_id = {r['request_id']: r for r in cache}
        for exclusion in exclusions:
            _require(exclusion['request_id'] in records_by_id, 'cache excluído ausente')
            record = records_by_id[exclusion['request_id']]
            excluded = excluded_pair_from_cache(record, records_by_key, by_id, config)
            validate_content_exclusion(exclusion, excluded, by_id)
            _require(excluded['id'] not in {p['id'] for p in pairs}, 'candidato rejeitado continua no dataset')
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
    if sealed and manifest['metadata']['purpose'] in {'frozen_operational_derivation', 'frozen_derivation_candidate'}:
        from hts_core.adapters.dataset_review import validate_review
        from hts_core.adapters.dataset_operational import verify_operational_requirements
        review = validate_review(read_json(folder/'review.json'), folder, manifest['metadata']['parent_version'])
        authorization = read_json(folder/'freeze-authorization.json')
        operational = manifest['metadata']['purpose'] == 'frozen_operational_derivation'
        _require(review['modality'] == ('automated_ai' if operational else 'human_individual') and all(r['decision'] == 'accept' for r in review['responses']), 'revisão congelada rejeitada/modalidade incorreta')
        _require(all(authorization.get(k) for k in ('approved', 'reference', 'review_scope_accepted', 'source_alerts_resolved', 'cache_verified', 'reproduction_verified')), 'autorização congelada incompleta')
        if operational:
            _require(authorization['purpose'] == 'operational_derivation', 'autorização congelada incompatível')
            verify_operational_requirements(folder, authorization)
    return {'status': 'structurally_valid', 'sources': len(sources), 'groups': len(group_splits), 'pairs': len(pairs),
            'sentences': sum(len(p['sentences']) for p in pairs), 'formats': len(formats),
            'distribution': dict(sorted(distribution.items())), 'near_duplicate_links': near_alerts,
            'shared_sentence_alerts': shared, 'human_review': 'not_performed' if config['purpose'] == 'operational_derivation' else 'pending',
            'validation_modality': 'structural_and_provenance',
            'content_assessment': 'automated_ai_not_independent' if sealed and manifest['metadata']['purpose'] == 'frozen_operational_derivation' else 'separate_record',
            'semantic_training_ready': False, 'semantic_quality': 'not_certified',
            'limits': 'shingle detector and exact matches do not rule out all semantic overlap'}


def _check_config(config):
    allowed = {'purpose', 'scientific_approval', 'seed', 'split_percent', 'segment_sentences', 'minimum_sentences',
               'minimum_sentence_words', 'near_duplicate_threshold', 'shingle_size', 'edit_rates', 'insertion_proportions',
               'patchwork_sources', 'themes', 'limitations', 'approval_reference', 'source_plan_reference', 'review_policy',
               'authorization_reference', 'required_types', 'format_policy', 'generated_policy', 'c3_definition',
               'c6_definition', 'assessment', 'use_limits', 'content_exclusion_policy', 'record_contract', 'curation_policy', 'source_exclusions'}
    _require(not set(config) - allowed, 'campos desconhecidos na configuração')
    _require(config['purpose'] in {'pilot', 'source_preparation', 'experimental_candidate', 'operational_derivation'}, 'finalidade inválida')
    _require(type(config['seed']) is int, 'seed inválida')
    _require(config['split_percent'] and len(config['split_percent']) == 3 and all(type(n) is int and n > 0 for n in config['split_percent']) and sum(config['split_percent']) == 100, 'split inválido')
    _require(type(config['segment_sentences']) is int and type(config['minimum_sentences']) is int and 1 <= config['minimum_sentences'] <= config['segment_sentences'], 'limites de seleção inválidos')
    _require(type(config['minimum_sentence_words']) is int and config['minimum_sentence_words'] >= 1, 'mínimo de palavras inválido')
    _require(type(config['shingle_size']) is int and config['shingle_size'] >= 1 and 0 < config['near_duplicate_threshold'] <= 1, 'agrupamento inválido')
    for key in ('edit_rates', 'insertion_proportions'):
        values = config[key]
        _require(values and len(values) == len(set(values)) and all(type(v) in {int, float} and 0 < v < 1 for v in values), 'taxas inválidas')
    _require(config['patchwork_sources'] and all(type(v) is int and 2 <= v <= 4 for v in config['patchwork_sources']), 'origens patchwork inválidas')
    if config['purpose'] == 'operational_derivation':
        from hts_core.adapters.dataset_operational import check_generated_policy
        check_generated_policy(config.get('generated_policy'))
        assessment = config.get('assessment', {})
        _require(set(assessment) == {'modality', 'independent_of_generator', 'human_review', 'acceptance', 'intense_c2', 'rejections'}
                 and assessment['modality'] == 'automated_ai' and assessment['independent_of_generator'] is False
                 and assessment['human_review'] == 'not_performed'
                 and all(isinstance(assessment[k], str) and assessment[k] for k in ('acceptance', 'intense_c2', 'rejections')),
                 'modalidade/alcance da avaliação operacional inválidos')
        _require(config.get('authorization_reference') and config.get('required_types') == [f'C{i}' for i in range(8)], 'especificação operacional incompleta')
        _require(config.get('review_policy') == 'all_generated_plus_first_id_per_split_method_severity_v1' and config.get('format_policy') == 'first_content_per_split_method_severity_plus_length_extremes_v1', 'políticas operacionais desconhecidas')
    _require(config.get('record_contract') in {None, 'assessment_v2'}, 'contrato de registros desconhecido')
    _require(config.get('curation_policy') in {None, 'raw_templates_segment_v1'}, 'política de curadoria desconhecida')
    if config.get('curation_policy'):
        _require(config.get('source_exclusions') == {'Cerâmica': 'historical_source_resegmentation_exclusion_preserved'}, 'exclusão histórica de Cerâmica obrigatória nesta política')


def _check_rows(rows, text, context):
    from hts_core.domain.dataset import stable_id
    _require([s['position'] for s in rows] == list(range(len(rows))), 'posições inconsistentes')
    _require(len({s['id'] for s in rows}) == len(rows), 'IDs de sentença repetidos')
    _require(all(s['id'] == stable_id(context, str(s['position']), s['text']) for s in rows), 'identidade da sentença divergente')
    _require([s['text'] for s in rows] == split_sentences(clean_extracted(text)), 'resegmentação divergente')
    _require(all(s['words'] == word_count(s['text']) for s in rows), 'contagem de palavras divergente')
    _require(all(s['semantic'] == semantic_text(s['text']) for s in rows), 'perfil semântico divergente')
    _require(all(s['lexical'] == list(_expected_lexical(s['text'])) for s in rows), 'perfil lexical divergente do processamento')


@lru_cache(maxsize=4096)
def _expected_lexical(text):
    from hts_core.adapters import nlp
    from hts_core.domain.preprocess import lexical_tokens
    return tuple(lexical_tokens(text, nlp.analyze, nlp.STOPWORDS))


def _check_transformation(pair, sources, origins, config):
    kind, method = pair['synthetic_type'], pair['method']
    allowed = {'C0': {'negative_easy', 'negative_hard'}, 'C1': {'copy'}, 'C2': {'character_substitution'},
               'C3': {'insert'}, 'C4': {'patchwork'}, 'C5': {'llm_direct', 'backtranslation'},
               'C6': {'phrase_guided_rewrite'}, 'C7': {'reorder'}}
    _require(method in allowed[kind], 'classe/operação incompatíveis')
    fixed_severity = {'C0': 'easy' if method == 'negative_easy' else 'hard', 'C1': 'none', 'C5': 'uncalibrated', 'C6': 'uncalibrated', 'C7': 'permutation'}
    _require(kind not in fixed_severity or pair['severity'] == fixed_severity[kind], 'severidade incompatível com método')
    generation_keys = {'C0': {'donor', 'semantic_dissimilarity'}, 'C1': set(),
                       'C2': {'requested_rate', 'by_sentence', 'semantic_preservation'},
                       'C3': {'requested_proportion', 'focal_count', 'total_count', 'donor'},
                       'C4': {'sources'}, 'C5': {'cache_key', 'cache_request_id', 'semantic_quality'},
                       'C6': {'cache_key', 'cache_request_id', 'semantic_quality'}, 'C7': {'permutation'}}
    _require(set(pair['generation']) == generation_keys[kind], 'schema de operação incompleto/desconhecido')
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
        _require(donor['group'] != sources[pair['source_id']]['group'], 'negativo da mesma família')
        _require([r['ancestors'][0]['sentence_id'] for r in rows] == [r['id'] for r in donor['sentences']], 'doador/conteúdo do negativo divergente')
        _require((donor['theme'] == sources[pair['source_id']]['theme']) == (method == 'negative_hard'), 'tema do negativo inválido')
    if kind == 'C1':
        _require(pair['text'] == ' '.join(r['text'] for r in sources[pair['source_id']]['sentences']), 'C1 não é igualdade contratada')
    if kind == 'C7':
        order = pair['generation']['permutation']
        original = sources[pair['source_id']]['sentences']
        _require(sorted(order) == list(range(len(original))) and order != list(range(len(original))), 'permutação inválida/sem efeito')
        _require([r['ancestors'][0]['sentence_id'] for r in rows] == [original[i]['id'] for i in order], 'permutação/proveniência divergentes')
        _require(pair['text'] != ' '.join(r['text'] for r in original), 'permutação textual sem efeito')
    if kind == 'C2':
        infos = pair['generation']['by_sentence']
        rate = pair['generation']['requested_rate']
        _require(rate in config['edit_rates'] and pair['severity'] == str(rate), 'taxa/severidade C2 fora da configuração')
        _require(len(infos) == len(rows), 'edições/sentenças divergentes')
        _require(any(info['realized_count'] > 0 for info in infos), 'edição textual sem efeito')
        for row, info in zip(rows, infos):
            _require(len(row['ancestors']) == 1 and row['ancestors'][0]['sentence_id'] == info['source_sentence_id'], 'edição/proveniência divergente')
            original = origins[info['source_sentence_id']][1]['text']
            output, seen = list(original), set()
            for op in info['operations']:
                pos = op['position']
                _require(0 <= pos < len(output) and pos not in seen, 'posição de edição inválida')
                _require(op['before'] == original[pos] and op['after'] != op['before'] and len(op['after']) == 1, 'edição sem efeito/incorreta')
                _require(original[pos].isalpha() and original[pos].islower() and op['operation'] == 'substitute' and op['after'] == ('z' if original[pos] == 'x' else 'x'), 'substituição fora do contrato')
                seen.add(pos)
                output[pos] = op['after']
            eligible = sum(c.isalpha() and c.islower() for c in original)
            _require(info['eligible'] == eligible and info['realized_count'] == len(seen), 'contagem de edição inválida')
            _require(info['realized_rate'] == (len(seen) / eligible if eligible else 0), 'taxa realizada inválida')
            _require(''.join(output) == row['text'], 'saída não corresponde às operações')
            _require(len(seen) == min(eligible, int(eligible * info['requested_rate'] + .5)), 'quantidade não corresponde à taxa solicitada')
            from hts_core.domain.strings import levenshtein_distance
            _require(info['requested_rate'] == rate and info['effective_levenshtein'] == levenshtein_distance(original, row['text']), 'metadados de edição divergentes')
    if kind == 'C3':
        info = pair['generation']
        _require(0 < pair['r']['numerator'] < len(rows), 'inserção não mistura origens')
        _require(info['total_count'] == len(rows) and info['focal_count'] == pair['r']['numerator'], 'composição C3 divergente')
        focal, donor = sources[pair['source_id']], sources[info['donor']]
        proportion = info['requested_proportion']
        total = min(len(focal['sentences']), len(donor['sentences']))
        count = int(total * proportion + .5)
        expected = focal['sentences'][:count] + donor['sentences'][:total-count]
        _require(proportion in config['insertion_proportions'] and pair['severity'] == str(proportion), 'proporção/severidade C3 divergentes')
        _require(donor['group'] != focal['group'] and total == len(rows) and [r['ancestors'][0]['sentence_id'] for r in rows] == [r['id'] for r in expected], 'ordem/doador C3 divergentes')
    if kind == 'C4':
        actual = {a['source_id'] for r in rows for a in r['ancestors']}
        declared = pair['generation']['sources']
        _require(2 <= len(actual) <= 4 and set(declared) == actual and len(declared) == len(actual) and pair['severity'] == str(len(actual)) and len(actual) in config['patchwork_sources'], 'patchwork/origens/severidade divergentes')
        _require(declared[0] == pair['source_id'] and len({sources[s]['group'] for s in declared}) == len(declared), 'famílias patchwork divergentes')
        expected = [sources[declared[i % len(declared)]]['sentences'][i // len(declared)]['id'] for i in range(len(rows))]
        _require([r['ancestors'][0]['sentence_id'] for r in rows] == expected, 'alternância patchwork divergente')
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
    from hts_core.adapters.idf_contract import lexical_projection, validate_training_idf_contract
    from hts_core.application.text_pipeline import prepare_sentences
    from hts_core.application.dataset_pipeline import pipeline_descriptor
    validate_data(folder)
    report = validate_training_idf_contract(folder, idf_folder)
    descriptor = read_json(Path(idf_folder)/'construction.json')
    _require(lexical_projection(descriptor['pipeline']) == lexical_projection(pipeline_descriptor()),
             'produtor lexical/modelo/recursos diferem do ambiente atual; preservar e usar o ambiente identificado')
    counts = Counter()
    for source in read_jsonl(Path(folder)/'sources.jsonl'):
        if source['split'] == 'train':
            unique = {t for row in prepare_sentences(source['text'], nlp.analyze, nlp.STOPWORDS) for t in row.lexical}
            counts.update(unique)
    table = read_json(Path(idf_folder)/'idf.json')
    _require(table['df'] == dict(counts), 'df do IDF divergente do treino recomputado')
    return {**report, 'status': 'training_only_verified', 'sources': table['n_docs'],
            'current_runtime_producer_equivalence': 'verified_lexical_dependencies_only',
            'lexical_recomputation': 'executed', 'scope': 'A_B_and_C_verified'}
