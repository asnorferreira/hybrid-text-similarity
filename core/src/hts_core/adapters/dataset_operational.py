from collections import Counter
from pathlib import Path

from hts_core.adapters.dataset_store import digest, identity, inside, read_json, read_jsonl, seal, verify_seal, write_json, write_jsonl, write_new


def verify_source_origin(source, folder):
    folder = Path(folder)
    upstream = read_json(folder/'upstream-manifest.json')
    matches = [e for e in upstream['documents'] if e['pageid'] == source['pageid'] and e['revid'] == source['revision']]
    if len(matches) != 1:
        raise ValueError('fonte não pertence à revisão coletada')
    entry = matches[0]
    response = inside(folder, 'provenance/' + entry['response_file']).read_bytes()
    rights_bytes = (folder/'provenance/rightsinfo-response.json').read_bytes()
    if digest(response) != entry['response_sha256'] or digest(rights_bytes) != upstream['rightsinfo_sha256']:
        raise ValueError('resposta da origem/direitos divergente')
    page = __import__('json').loads(response)['query']['pages'][0]
    revision = page['revisions'][0]
    rights = __import__('json').loads(rights_bytes)['query']['rightsinfo']
    raw = revision['slots']['main']['content'].encode('utf-8')
    if page['pageid'] != source['pageid'] or revision['revid'] != source['revision'] or digest(raw) != source['raw_sha256']:
        raise ValueError('raw/pageid/revisão incompatível com resposta da origem')
    expected = {'title': page['title'], 'license': rights['text'], 'license_reference': rights['url'],
                'url': entry['url'], 'history_url': entry['history_url'], 'collected_utc': entry['retrieved_at']}
    if any(source[k] != v for k, v in expected.items()):
        raise ValueError('metadados/atribuição da origem divergentes')
    return {'procedure': 'saved_official_API_revision_content_and_site_rights_crosscheck_v1',
            'response_sha256': entry['response_sha256'], 'rightsinfo_sha256': upstream['rightsinfo_sha256'],
            'attribution': 'Wikipedia contributors; title, fixed revision URL and author history URL retained',
            'scope': 'declared source metadata checked automatically against saved collection responses; not legal review or individual imported-content clearance',
            'human_review': False, 'legal_review': False}


def build_operational(preparation, collection, configuration, destination):
    from hts_core.application.dataset_pipeline import generate_pairs, pipeline_descriptor
    from hts_core.adapters.dataset_validation import validate_data
    preparation, collection, destination = Path(preparation), Path(collection), Path(destination)
    parent = verify_seal(preparation)
    validate_data(preparation)
    if configuration['purpose'] != 'operational_derivation' or not configuration.get('authorization_reference'):
        raise PermissionError('finalidade operacional e autorização explícitas obrigatórias')
    config = {**configuration, 'themes': read_json(preparation/'config.json')['themes']}
    previous = read_json(preparation/'config.json')
    keys = ('seed', 'split_percent', 'segment_sentences', 'minimum_sentences', 'minimum_sentence_words', 'near_duplicate_threshold', 'shingle_size')
    if any(config[k] != previous[k] for k in keys):
        raise ValueError('alteração de fontes/splits/seleção exige nova preparação, não migração silenciosa')
    destination.mkdir(parents=True, exist_ok=False)
    for name in parent['files']:
        if name.startswith('sources/') or name in {'selection.json', 'upstream-manifest.json', 'group-alerts.json'}:
            write_new(destination/name, (preparation/name).read_bytes())
    write_new(destination/'provenance/rightsinfo-response.json', (collection/'rightsinfo-response.json').read_bytes())
    upstream = read_json(collection/'manifest.json')
    for entry in upstream['documents']:
        write_new(inside(destination, 'provenance/' + entry['response_file']), inside(collection, entry['response_file']).read_bytes())
    sources = read_jsonl(preparation/'sources.jsonl')
    for source in sources:
        source['provenance_verification'] = verify_source_origin(source, destination)
        source['license_status'] = 'source_verified'
        source['exposure'] = 'construction_inspected_no_predictive_use'
    write_json(destination/'config.json', config)
    write_json(destination/'pipeline.json', pipeline_descriptor())
    write_jsonl(destination/'sources.jsonl', sources)
    pairs, rejected = generate_pairs(sources, config)
    write_jsonl(destination/'pairs.jsonl', pairs)
    write_json(destination/'rejections.json', rejected)
    write_json(destination/'validation.json', validate_data(destination, sealed=False))
    return seal(destination, {'purpose': 'operational_derivation', 'state': 'candidate', 'parent_version': parent['version'],
                              'config_identity': identity(config), 'assessment_modality': 'structural_only',
                              'human_review': 'not_performed', 'semantic_training_ready': False})


def selected_format_contents(pairs):
    selected = set()
    for stratum in sorted({(p['split'], p['method'], p['severity']) for p in pairs}):
        selected.add(min(p['content_id'] for p in pairs if (p['split'], p['method'], p['severity']) == stratum))
    if pairs:
        ordered = sorted(pairs, key=lambda p: (len(p['text']), p['content_id']))
        selected.update([ordered[0]['content_id'], ordered[-1]['content_id']])
    return sorted(selected)


def excluded_pair_from_cache(record, records, sources, config):
    from hts_core.adapters.dataset_llm import validate_lineage
    from hts_core.domain.text import clean_extracted
    from hts_core.domain.dataset import stable_id
    output, source = validate_lineage(record, records, sources)
    method = {'translate_to_pt': 'backtranslation'}.get(record['request']['method'], record['request']['method'])
    if method not in {'llm_direct', 'backtranslation', 'phrase_guided_rewrite'}:
        raise ValueError('não excluir intermediário como candidato final')
    kind = 'C6' if method == 'phrase_guided_rewrite' else 'C5'
    text = clean_extracted(' '.join(r['text'] for r in output))
    cid = identity({'text': text})
    return {'id': stable_id(source['id'], kind, method, 'uncalibrated', str(config['seed']), cid),
            'source_id': source['id'], 'source_ids': [source['id']], 'split': source['split'], 'synthetic_type': kind,
            'method': method, 'severity': 'uncalibrated', 'text': text,
            'generation': {'cache_key': record['cache_key'], 'cache_request_id': record['request_id'], 'semantic_quality': 'human_pending'}}


def validate_content_exclusion(exclusion, pair, sources):
    from datetime import datetime
    from hts_core.adapters.dataset_review import review_item
    if set(exclusion) != {'request_id', 'pair_id', 'review_dataset_version', 'review_identity', 'item', 'response'}:
        raise ValueError('schema de exclusão inválido')
    if exclusion['pair_id'] != pair['id'] or exclusion['request_id'] != pair['generation']['cache_request_id']:
        raise ValueError('exclusão de outro cache/par')
    item, response = exclusion['item'], exclusion['response']
    if item != review_item(pair, sources) or response['id'] != pair['id'] or response['item_sha256'] != identity(item):
        raise ValueError('texto/operação/identidade da exclusão divergentes')
    if response['decision'] != 'reject' or not response['reason'] or response['generator_relation'] != 'same_agent_as_generator_not_independent':
        raise ValueError('exclusão sem rejeição automatizada identificada')
    datetime.fromisoformat(response['date'])
    if not exclusion['review_dataset_version'] or not exclusion['review_identity'] or not response['findings']:
        raise ValueError('origem/motivos localizados da exclusão ausentes')
    originals = '\n'.join(s['text'] for s in item['source_texts'])
    for finding in response['findings']:
        if not finding['source_quote'] or not finding['output_quote'] or finding['source_quote'] not in originals or finding['output_quote'] not in pair['text']:
            raise ValueError('trechos da exclusão não correspondem à fonte/saída')
    return exclusion


def coverage(folder):
    folder = Path(folder)
    sources, pairs = read_jsonl(folder/'sources.jsonl'), read_jsonl(folder/'pairs.jsonl')
    formats = read_jsonl(folder/'formats.jsonl') if (folder/'formats.jsonl').exists() else []
    counts = lambda values: dict(sorted(Counter(values).items()))
    return {'sources': len(sources), 'groups': len({s['group'] for s in sources}), 'pairs': len(pairs),
            'distinct_contents': len({p['content_id'] for p in pairs}), 'sentence_records': sum(len(p['sentences']) for p in pairs),
            'sources_by_theme': counts(s['theme'] for s in sources),
            'groups_by_split_theme': counts(s['split'] + ':' + s['theme'] for s in {s['group']: s for s in sources}.values()),
            'pairs_by_type': counts(p['synthetic_type'] for p in pairs),
            'pairs_by_split_method_severity': counts(':'.join((p['split'], p['method'], p['severity'])) for p in pairs),
            'sentences_by_split_method': dict(sorted((key, sum(len(p['sentences']) for p in pairs if p['split'] + ':' + p['method'] == key)) for key in {p['split'] + ':' + p['method'] for p in pairs})),
            'generated_by_split_theme_method': counts(':'.join((p['split'], next(s['theme'] for s in sources if s['id'] == p['source_id']), p['method'])) for p in pairs if p['synthetic_type'] in {'C5', 'C6'}),
            'generated_sources': len({p['source_id'] for p in pairs if p['synthetic_type'] in {'C5', 'C6'}}),
            'sentences_by_split_method_severity': dict(sorted((key, sum(len(p['sentences']) for p in pairs if ':'.join((p['split'], p['method'], p['severity'])) == key)) for key in {':'.join((p['split'], p['method'], p['severity'])) for p in pairs})),
            'reuse_fraction_distribution': counts(str(p['r']['numerator']) + '/' + str(p['r']['denominator']) for p in pairs),
            'documented_content_exclusions': len(read_json(folder/'content-exclusions.json')) if (folder/'content-exclusions.json').exists() else 0,
            'formats': len(formats), 'format_contents': len({f['content_id'] for f in formats}),
            'formats_by_content': {cid: sorted(f['kind'] for f in formats if f['content_id'] == cid) for cid in sorted({f['content_id'] for f in formats})},
            'formats_by_split_kind': counts(f['split'] + ':' + f['kind'] for f in formats),
            'source_dependencies': 'pairs/sentences/content repetitions/formats from the same group are not independent'}


def verify_operational_requirements(folder, authorization):
    folder = Path(folder)
    manifest = verify_seal(folder)
    config = read_json(folder/'config.json')
    sources, pairs = read_jsonl(folder/'sources.jsonl'), read_jsonl(folder/'pairs.jsonl')
    themes = {s['theme'] for s in sources}
    generated = [p for p in pairs if p['synthetic_type'] in {'C5', 'C6'}]
    policy = config['generated_policy']
    if len({p['source_id'] for p in generated}) > policy['maximum_sources'] or len(list((folder/'cache').glob('*.json'))) > policy['maximum_records']:
        raise ValueError('limite de geração ultrapassado')
    if any(len(p['sentences']) != (policy['c6_sentences'] if p['synthetic_type'] == 'C6' else policy['source_sentences']) for p in generated):
        raise ValueError('tamanho da entrada gerada diverge do desenho')
    for source in sources:
        if source['provenance_verification'] != verify_source_origin(source, folder):
            raise ValueError('procedência técnica não conferida')
    expected_conditions = [('negative_easy', 'easy'), ('negative_hard', 'hard'), ('copy', 'none'), ('reorder', 'permutation')]
    expected_conditions += [('character_substitution', str(v)) for v in config['edit_rates']]
    expected_conditions += [('insert', str(v)) for v in config['insertion_proportions']]
    expected_conditions += [('patchwork', str(v)) for v in config['patchwork_sources']]
    for split in ('train', 'validation', 'test'):
        observed = {(p['method'], p['severity']) for p in pairs if p['split'] == split}
        if not set(expected_conditions) <= observed:
            raise ValueError('células operacionais método/severidade/split ausentes')
        for theme in themes:
            eligible = {s['id'] for s in sources if s['split'] == split and s['theme'] == theme}
            for method in config['generated_policy']['methods']:
                if not any(p['source_id'] in eligible and p['method'] == method for p in pairs):
                    raise ValueError('cobertura gerada método/tema/split incompleta')
    formats = read_jsonl(folder/'formats.jsonl')
    selected = selected_format_contents(pairs)
    expected = {(cid, kind) for cid in selected for kind in ('pdf', 'docx', 'txt')}
    if {(f['content_id'], f['kind']) for f in formats} != expected or len(formats) != len(expected):
        raise ValueError('cobertura de formatos incompleta/duplicada')
    proof = authorization.get('reproduction', {})
    expected_version = manifest['metadata'].get('parent_version') if manifest['metadata']['purpose'] == 'frozen_operational_derivation' else manifest['version']
    if not proof or proof.get('original_version') != expected_version or proof.get('reconstructed_version') != expected_version or proof.get('hashseeds') != ['1', '917'] or not proof.get('isolated_public_copy'):
        raise ValueError('reprodução isolada não verificada/vinculada à versão')
    payload = {k: v for k, v in manifest['files'].items() if k not in {'review.json', 'freeze-authorization.json'}}
    if proof.get('file_inventory_sha256') != identity(payload):
        raise ValueError('inventário reconstruído não corresponde aos arquivos do candidato')
    return coverage(folder)


def operational_authorization(folder, reproduction):
    from hts_core.adapters.dataset_validation import validate_data
    folder = Path(folder)
    config = read_json(folder/'config.json')
    report = validate_data(folder)
    if config['purpose'] != 'operational_derivation':
        raise PermissionError('autorização automática restrita ao contrato operacional do autor')
    if report['near_duplicate_links'] or report['shared_sentence_alerts']:
        raise ValueError('alertas exigem resolução técnica registrada; não aprovar silenciosamente')
    authorization = {'purpose': 'operational_derivation', 'approved': True, 'reference': config['authorization_reference'],
                     'approval_scope': 'author_task_authorization_not_human_review_or_scientific_approval',
                     'review_scope_accepted': True, 'source_alerts_resolved': True, 'cache_verified': True,
                     'reproduction_verified': True, 'reproduction': reproduction}
    verify_operational_requirements(folder, authorization)
    return authorization
