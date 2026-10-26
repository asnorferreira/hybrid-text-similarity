from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import importlib.metadata
import importlib.util
from pathlib import Path
import platform

from hts_core.adapters import nlp
from hts_core.adapters.dataset_store import canonical, digest, identity, inside, read_json, seal, write_json, write_jsonl, write_new
from hts_core.adapters.refcorpus import wikitext_to_text
from hts_core.application.text_pipeline import prepare_sentences
from hts_core.domain.dataset import edit_characters, ranked, reorder_indices, reuse_fraction, source_groups, split_groups, stable_id
from hts_core.domain.lexical import document_frequencies
from hts_core.domain.strings import levenshtein_distance
from hts_core.domain.text import clean_extracted, split_sentences

CORE = Path(__file__).resolve().parents[3]


def pipeline_descriptor():
    paths = ['domain/text.py', 'domain/preprocess.py', 'domain/dataset.py', 'domain/lexical.py',
             'application/text_pipeline.py', 'application/dataset_pipeline.py', 'adapters/nlp.py',
             'adapters/refcorpus.py', 'adapters/dataset_schemas.py', 'adapters/dataset_validation.py',
             'adapters/dataset_formats.py', 'adapters/dataset_llm.py', 'adapters/dataset_store.py',
             'adapters/dataset_collect.py', 'adapters/dataset_review.py', 'adapters/dataset_mongo.py',
             'adapters/dataset_operational.py', 'adapters/dataset_curation.py', 'domain/strings.py', 'cli/dataset.py']
    model_spec = importlib.util.find_spec(nlp.SPACY_MODEL)
    if model_spec is None or model_spec.origin is None:
        raise ImportError('spaCy model module has no filesystem origin')
    model_root = Path(model_spec.origin).parent
    text_hash = lambda p: digest(p.read_bytes().replace(b'\r\n', b'\n'))
    return {'text_hash_policy': 'UTF-8 source/config/lock text CRLF normalized to LF; binary assets unchanged',
            'code': {p: text_hash(CORE/'src/hts_core'/p) for p in paths},
            'generator_scripts': {name: text_hash(CORE/'scripts'/name) for name in ['prepare_dataset_sources.py', 'rebuild_dataset_operational.py']},
            'font_assets': {p.relative_to(CORE).as_posix(): digest(p.read_bytes()) if p.suffix == '.ttf' else text_hash(p) for p in sorted((CORE/'assets/fonts').glob('*')) if p.is_file()},
            'lock_sha256': text_hash(CORE/'uv.lock'), 'model': nlp.model_info(),
            'model_assets': {p.relative_to(model_root).as_posix(): digest(p.read_bytes()) for p in sorted(model_root.rglob('*'))
                             if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'},
            'stopwords': sorted(nlp.STOPWORDS), 'disabled': ['parser', 'ner'],
            'packages': {p: importlib.metadata.version(p) for p in ['spacy', 'pt-core-news-sm', 'numpy', 'mwparserfromhell',
                                                                  'pydantic', 'reportlab', 'python-docx']},
            'python': platform.python_version(), 'unicode': __import__('unicodedata').unidata_version}


def sentence_records(text, context, ancestors=None, method='source', parameters=None, intended=None):
    prepared = prepare_sentences(clean_extracted(text), nlp.analyze, nlp.STOPWORDS)
    if ancestors is not None and len(prepared) != len(ancestors):
        raise ValueError('resegmentação impede atribuição um a um; preservar candidato como rejeitado')
    return [{'id': stable_id(context, str(s.index), s.raw), 'position': s.index, 'text': s.raw,
             'semantic': s.semantic, 'lexical': list(s.lexical), 'words': s.words,
             'ancestors': ancestors[s.index] if ancestors is not None else [], 'transformation': method,
             'parameters': parameters or {}, 'intended_class': intended, 'validated_class': None,
             'semantic_target': None, 'validation': 'human_pending' if method != 'source' else 'structural'}
            for s in prepared]


def normalize_sources(entries, raw_loader, folder, config):
    sources, exclusions = [], []
    for entry in sorted(entries, key=lambda e: (e['pageid'], e['revid'])):
        if entry['title'] in config.get('source_exclusions', {}):
            exclusions.append({'id': f"wikipedia-pt-{entry['pageid']}-{entry['revid']}",
                               'reason': config['source_exclusions'][entry['title']]})
            continue
        raw = raw_loader(entry)
        if digest(raw) != entry['sha256']:
            raise ValueError('hash de origem divergente')
        sid = f"wikipedia-pt-{entry['pageid']}-{entry['revid']}"
        from hts_core.adapters.dataset_curation import extract_for_config
        if config.get('curation_policy'):
            from hts_core.adapters.dataset_curation import curated_text
            extracted, ledger = curated_text(raw.decode('utf-8'))
            write_json(Path(folder)/f'sources/{sid}.curation.json', ledger)
        else:
            extracted = extract_for_config(raw.decode('utf-8'), config)
        normalized = clean_extracted(extracted)
        base = f'sources/{sid}'
        for suffix, data in [('wiki', raw), ('extracted.txt', extracted.encode()), ('normalized.txt', normalized.encode())]:
            write_new(Path(folder)/f'{base}.{suffix}', data)
        all_sentences = split_sentences(normalized)
        eligible = [(i, s) for i, s in enumerate(all_sentences) if len(s.split()) >= config['minimum_sentence_words']]
        selected = eligible[:config['segment_sentences']]
        if len(selected) < config['minimum_sentences']:
            exclusions.append({'id': sid, 'reason': 'insufficient_eligible_sentences', 'available': len(selected)})
            continue
        records = sentence_records(' '.join(s for _, s in selected), sid)
        if len(records) != len(selected):
            exclusions.append({'id': sid, 'reason': 'source_resegmentation', 'available': len(selected)})
            continue
        for record, (position, _) in zip(records, selected):
            record['parameters'] = {'original_sentence_position': position}
        sources.append({'id': sid, 'title': entry['title'], 'url': entry['url'], 'provider': 'pt.wikipedia.org',
                        'pageid': entry['pageid'], 'revision': entry['revid'], 'collected_utc': entry['retrieved_at'],
                        'license': entry['license'], 'license_reference': entry.get('license_reference', entry['url']),
                        'license_status': entry.get('license_status', 'historical_declared'), 'history_url': entry['history_url'],
                        'raw_file': f'{base}.wiki', 'raw_sha256': digest(raw),
                        'extracted_file': f'{base}.extracted.txt', 'extracted_sha256': digest(extracted.encode()),
                        'normalized_file': f'{base}.normalized.txt', 'normalized_sha256': digest(normalized.encode()),
                        'text': normalized, 'language': 'pt-BR-expected',
                        'extraction': config.get('curation_policy', 'wikitext_to_text') + ' -> clean_extracted; discarded syntax remains in raw; first eligible sentences',
                        'theme': config.get('themes', {}).get(entry['title'], 'unspecified'),
                        'theme_origin': 'project_manual_pilot_mapping_not_Wikipedia_category',
                        'inclusion': 'included', 'inclusion_reason': 'minimum eligible segment; no prediction consulted',
                        'exposure': 'development_refcorpus' if config['purpose'] == 'pilot' else entry.get('exposure', 'unreviewed'),
                        'group': '', 'split': 'train', 'sentences': records})
        exclusions.append({'id': sid, 'reason': 'selection_ledger_not_source_exclusion', 'total_sentences': len(all_sentences),
                           'selected_positions': [p for p, _ in selected], 'unselected_count': len(all_sentences) - len(selected)})
    return sources, exclusions


def _make_pair(focal, components, synthetic_type, method, severity, seed, generation):
    text = ' '.join(item['text'] for item in components)
    cid = identity({'text': clean_extracted(text)})
    pid = stable_id(focal['id'], synthetic_type, method, severity, str(seed), cid)
    ancestry = [item['ancestors'] for item in components]
    intended = {'C1': 'copia_exata', 'C2': 'copia_editada', 'C5': 'parafrase', 'C6': None}.get(synthetic_type)
    records = sentence_records(text, pid, ancestry, method, generation, intended)
    if synthetic_type in {'C0', 'C1', 'C3', 'C4', 'C7'}:
        for row in records:
            row['intended_class'] = ('copia_exata' if any(a['source_id'] == focal['id'] for a in row['ancestors'])
                                     else 'negativo_por_construcao')
    source_ids = sorted({focal['id']} | {a['source_id'] for row in ancestry for a in row})
    return {'id': pid, 'content_id': cid, 'source_id': focal['id'], 'source_ids': source_ids,
            'split': focal['split'], 'synthetic_type': synthetic_type, 'method': method, 'severity': severity,
            'seed': seed, 'text': clean_extracted(text), 'sentences': records,
            'r': reuse_fraction(records, focal['id']), 'r_by_source': {s: reuse_fraction(records, s) for s in source_ids},
            'generation': generation, 'human_review': 'pending'}


def _components(source):
    return [{'text': row['text'], 'ancestors': [{'source_id': source['id'], 'sentence_id': row['id']}]}
            for row in source['sentences']]


def generate_pairs(sources, config):
    pairs, rejected = [], []
    seed = config['seed']
    for focal in sorted(sources, key=lambda s: s['id']):
        original = _components(focal)
        peers = [s for s in sources if s['split'] == focal['split'] and s['group'] != focal['group']]
        peers.sort(key=lambda s: stable_id(str(seed), focal['id'], s['id']))

        def add(kind, method, severity, components, parameters):
            try:
                pairs.append(_make_pair(focal, components, kind, method, severity, seed, parameters))
            except ValueError as exc:
                rejected.append({'source_id': focal['id'], 'type': kind, 'method': method, 'severity': severity,
                                 'reason': str(exc), 'components': components, 'parameters': parameters})

        add('C1', 'copy', 'none', original, {})
        permutation = reorder_indices(len(original), stable_id(str(seed), focal['id']))
        shuffled = [original[i] for i in permutation]
        if ' '.join(c['text'] for c in shuffled) == ' '.join(c['text'] for c in original):
            rejected.append({'source_id': focal['id'], 'type': 'C7', 'reason': 'no_textual_effect', 'permutation': permutation})
        else:
            add('C7', 'reorder', 'permutation', shuffled, {'permutation': permutation})
        for rate in config['edit_rates']:
            changed, operations = [], []
            for i, item in enumerate(original):
                text, info = edit_characters(item['text'], rate, stable_id(str(seed), focal['id'], str(i)))
                changed.append({**item, 'text': text})
                operations.append({'source_sentence_id': item['ancestors'][0]['sentence_id'], **info,
                                   'effective_levenshtein': levenshtein_distance(item['text'], text)})
            if not any(o['realized_count'] for o in operations):
                rejected.append({'source_id': focal['id'], 'type': 'C2', 'reason': 'no_effect', 'rate': rate})
            else:
                add('C2', 'character_substitution', str(rate), changed,
                    {'requested_rate': rate, 'by_sentence': operations, 'semantic_preservation': 'unverified'})
        for difficulty in ('easy', 'hard'):
            candidates = [p for p in peers if (p['theme'] == focal['theme']) == (difficulty == 'hard')]
            if candidates:
                add('C0', 'negative_' + difficulty, difficulty, _components(candidates[0]),
                    {'donor': candidates[0]['id'], 'semantic_dissimilarity': 'unverified'})
            else:
                rejected.append({'source_id': focal['id'], 'type': 'C0', 'method': difficulty, 'reason': 'no_same_split_donor'})
        if peers:
            donor = _components(peers[0])
            length = min(len(original), len(donor))
            for proportion in config['insertion_proportions']:
                count = int(length * proportion + .5)
                if not 0 < count < length:
                    raise ValueError('inserção deve conter ambas as origens')
                add('C3', 'insert', str(proportion), original[:count] + donor[:length - count],
                    {'requested_proportion': proportion, 'focal_count': count, 'total_count': length, 'donor': peers[0]['id']})
        for count in config['patchwork_sources']:
            donors = [focal, *peers[:count - 1]]
            if len(donors) != count:
                rejected.append({'source_id': focal['id'], 'type': 'C4', 'count': count, 'reason': 'insufficient_same_split_sources'})
                continue
            components = [_components(donors[i % count])[i // count] for i in range(len(original))]
            add('C4', 'patchwork', str(count), components, {'sources': [s['id'] for s in donors]})
    if config.get('record_contract') == 'assessment_v2':
        for pair in pairs:
            initialize_pair_states(pair)
    return sorted(pairs, key=lambda p: p['id']), rejected


def initialize_pair_states(pair):
    pair['human_review'] = 'not_performed'
    pair['content_assessment'] = {'status': 'not_assessed', 'scope': 'whole_pair_not_individual_sentences',
                                  'modality': None, 'review_identity': None, 'review_dataset_version': None,
                                  'response_id': None}
    for row in pair['sentences']:
        row['validation'] = 'structural'


def build_local(config, corpus, destination):
    if config['purpose'] not in {'pilot', 'experimental_candidate'}:
        raise ValueError('finalidade inválida')
    if config['purpose'] != 'pilot' and not (config.get('scientific_approval') and config.get('approval_reference')
                                            and config.get('source_plan_reference') and config.get('review_policy')):
        raise PermissionError('geração completa requer contrato experimental e escala aprovados')
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'config.json', config)
    write_json(destination/'pipeline.json', pipeline_descriptor())
    corpus = Path(corpus)
    manifest = read_json(corpus/'manifest.json')
    write_json(destination/'upstream-manifest.json', manifest)
    sources, exclusions = normalize_sources(manifest['documents'], lambda e: inside(corpus, e['file']).read_bytes(), destination, config)
    groups, alerts = source_groups(sources, config['near_duplicate_threshold'], config['shingle_size'])
    splits = split_groups(groups, config['seed'], tuple(config['split_percent']))
    for source in sources:
        source.update(group=groups[source['id']], split=splits[source['id']])
    pairs, rejected = generate_pairs(sources, config)
    write_jsonl(destination/'sources.jsonl', sources)
    write_jsonl(destination/'pairs.jsonl', pairs)
    write_json(destination/'selection.json', exclusions)
    write_json(destination/'groups.json', {'groups': groups, 'alerts': alerts, 'detector': 'word-shingle Jaccard; same page/exact always connected'})
    write_json(destination/'rejections.json', rejected)
    write_json(destination/'availability.json', {'C5': 'pending_model_budget_real_generation_and_review',
                                               'C6': 'pending_operational_definition_and_review', 'semantic_target': None})
    from hts_core.adapters.dataset_validation import validate_data
    report = validate_data(destination, sealed=False)
    write_json(destination/'validation.json', report)
    return seal(destination, {'purpose': config['purpose'],
                              'state': 'development_not_experimental' if config['purpose'] == 'pilot' else 'candidate_human_pending',
                              'config_identity': identity(config)})


def add_cached_candidates(folder, cache_records, destination, exclusions=None):
    from hts_core.adapters.dataset_llm import validate_lineage
    from hts_core.adapters.dataset_store import read_jsonl, verify_seal
    from hts_core.adapters.dataset_validation import validate_data
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    if manifest['metadata']['purpose'].startswith('frozen'):
        raise PermissionError('versão congelada não aceita mutação; reconstruir candidato em destino novo')
    if manifest['metadata']['purpose'] not in {'pilot', 'experimental_candidate', 'operational_derivation'}:
        raise PermissionError('incorporação exige versão candidata ou piloto')
    if (folder/'cache').exists() or (folder/'formats.jsonl').exists():
        raise ValueError('incorporação usa a base anterior ao cache/formatos; fornecer todos os lotes em nova construção')
    validate_data(folder)
    config = read_json(folder/'config.json')
    sources = {s['id']: s for s in read_jsonl(folder/'sources.jsonl')}
    sources_by_sent = {r['id']: (s, r) for s in sources.values() for r in s['sentences']}
    destination.mkdir(parents=True, exist_ok=False)
    for name in manifest['files']:
        if name not in {'pairs.jsonl', 'validation.json'}:
            write_new(destination/name, (folder/name).read_bytes())
    pairs, rejected = read_jsonl(folder/'pairs.jsonl'), []
    exclusions = [] if exclusions is None else exclusions
    excluded_by_request = {e['request_id']: e for e in exclusions}
    if len(excluded_by_request) != len(exclusions):
        raise ValueError('exclusões duplicadas')
    if exclusions and config.get('content_exclusion_policy') != 'documented_automated_assessment_exclusions_v1':
        raise ValueError('exclusão sem política operacional explícita')
    if config['purpose'] == 'operational_derivation':
        write_json(destination/'content-exclusions.json', exclusions)
    existing = [read_json(p) for p in sorted((folder/'cache').glob('*.json'))] if (folder/'cache').exists() else []
    all_records = existing + list(cache_records)
    if len({r['cache_key'] for r in all_records}) != len(all_records) or len({r['request_id'] for r in all_records}) != len(all_records):
        raise ValueError('IDs/chaves de cache duplicados; destino parcial preservado')
    cache_by_key = {r['cache_key']: r for r in all_records}
    for record in cache_records:
        write_json(inside(destination, 'cache/' + record['request_id'] + '.json'), record)
    for record in cache_records:
        try:
            spec = record['request']
            output, source = validate_lineage(record, cache_by_key, sources)
            method, original_inputs, synthetic_type = 'llm_direct', spec['input'], 'C5'
            if spec['method'] == 'translate_to_en':
                continue
            if spec['method'] == 'translate_to_pt':
                first = cache_by_key[spec['context']['parent_cache_key']]
                translated = first['structured']['sentences']
                expected_input = [{'id': row['source_sentence_ids'][0], 'text': row['text']} for row in translated]
                if first['request']['method'] != 'translate_to_en' or spec['input'] != expected_input:
                    raise ValueError('cadeia de retrotradução divergente')
                method, original_inputs = 'backtranslation', first['request']['input']
            elif spec['method'] == 'phrase_guided_rewrite' and config['purpose'] in {'pilot', 'operational_derivation'}:
                if not spec['context'].get('approval_reference') or not spec['context'].get('source_phrase'):
                    raise ValueError('C6 piloto exige origem e aprovação explícitas')
                if spec['context']['source_phrase'] not in original_inputs[0]['text']:
                    raise ValueError('frase C6 não pertence à origem')
                method, synthetic_type = 'phrase_guided_rewrite', 'C6'
            elif spec['method'] != 'llm_direct':
                raise ValueError('C6 aguarda definição operacional aprovada; cache preservado')
            source_ids = {sources_by_sent[r['id']][0]['id'] for r in original_inputs}
            if len(source_ids) != 1:
                raise ValueError('candidato direto deve pertencer a uma única fonte conhecida')
            source = sources[next(iter(source_ids))]
            if any(r['text'] != sources_by_sent[r['id']][1]['text'] for r in original_inputs):
                raise ValueError('entrada do cache não corresponde à origem')
            components = [{'text': r['text'], 'ancestors': [{'source_id': source['id'], 'sentence_id': sid} for sid in r['source_sentence_ids']]}
                          for r in output]
            pair = _make_pair(source, components, synthetic_type, method, 'uncalibrated', config['seed'],
                              {'cache_key': record['cache_key'], 'cache_request_id': record['request_id'], 'semantic_quality': 'human_pending'})
            if config['purpose'] == 'operational_derivation':
                for row in pair['sentences']:
                    row['intended_class'] = None
            if record['request_id'] in excluded_by_request:
                from hts_core.adapters.dataset_operational import validate_content_exclusion
                exclusion = validate_content_exclusion(excluded_by_request[record['request_id']], pair, sources)
                rejected.append({'request_id': record['request_id'], 'pair_id': pair['id'],
                                 'status': 'documented_content_exclusion', 'reason': exclusion['response']['reason']})
                continue
            if pair['id'] in {p['id'] for p in pairs}:
                raise ValueError('candidato já presente; não duplicar observação')
            if config.get('record_contract') == 'assessment_v2':
                initialize_pair_states(pair)
            pairs.append(pair)
        except (ValueError, KeyError, TypeError) as exc:
            rejected.append({'request_id': record['request_id'], 'reason': str(exc), 'status': 'rejected_not_deleted'})
    write_jsonl(destination/'pairs.jsonl', sorted(pairs, key=lambda p: p['id']))
    write_json(destination/'llm-rejections.json', rejected)
    write_json(destination/'validation.json', validate_data(destination, sealed=False))
    return seal(destination, {**manifest['metadata'], 'parent_version': manifest['version'],
                              'state': 'candidate_with_rejections' if any(r['status'] != 'documented_content_exclusion' for r in rejected) else 'candidate_assessment_pending',
                              'cache_rejections': sum(r['status'] != 'documented_content_exclusion' for r in rejected),
                              'documented_content_exclusions': sum(r['status'] == 'documented_content_exclusion' for r in rejected)})


def build_training_idf(folder, destination):
    from hts_core.adapters.dataset_validation import validate_data
    from hts_core.adapters.dataset_store import read_jsonl, verify_seal
    manifest = verify_seal(folder)
    validate_data(folder)
    sources = [s for s in read_jsonl(Path(folder)/'sources.jsonl') if s['split'] == 'train']
    if not sources:
        raise ValueError('nenhuma fonte de treino')
    tokenized = [[token for row in prepare_sentences(s['text'], nlp.analyze, nlp.STOPWORDS) for token in row.lexical] for s in sources]
    n_docs, df = document_frequencies(tokenized)
    table = {'n_docs': n_docs, 'df': dict(sorted(df.items())), 'formula': 'ln((1+N)/(1+df))+1',
             'tf': 'raw_count', 'unknown_df': 0, 'vector_normalization': 'cosine_only'}
    descriptor = {'purpose': read_json(Path(folder)/'config.json')['purpose'], 'construction_attestation': True,
                  'allowed_split': 'train', 'training_sources': [{k: s[k] for k in ('id', 'revision', 'raw_sha256', 'normalized_sha256')} for s in sources],
                  'pipeline': pipeline_descriptor(), 'table_content_sha256': identity(table),
                  'config': read_json(Path(folder)/'config.json'),
                  'input_identity': identity([{'id': s['id'], 'text': s['text']} for s in sources])}
    version = identity(descriptor)
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'idf.json', {**table, 'version': version})
    write_json(destination/'construction.json', {**descriptor, 'identity': version})
    write_json(destination/'execution.json', {'dataset_version': manifest['version'], 'constructed_utc': datetime.now(timezone.utc).isoformat(),
                                             'platform': platform.platform(), 'serialized_table_sha256': digest((destination/'idf.json').read_bytes())})
    return {'version': version, 'n_docs': n_docs, 'terms': len(df), 'purpose': descriptor['purpose']}
