from copy import deepcopy
import json
from pathlib import Path

import pytest

from tests.test_dataset_s4 import dataset, clone_unsealed, replace_jsonl
from hts_core.adapters.dataset_llm import record_session_candidate, session_candidate_spec
from hts_core.adapters.dataset_review import freeze, import_review, prepare_review, validate_review, prepare_automated_review, import_automated_review
from hts_core.adapters.dataset_formats import add_formats
from hts_core.adapters.dataset_store import canonical, digest, identity, read_json, read_jsonl, seal, verify_seal, write_json
from hts_core.adapters.dataset_validation import validate_data
from hts_core.application.dataset_pipeline import add_cached_candidates


@pytest.fixture(scope='module')
def llm_dataset(dataset, tmp_path_factory):
    # Registros artificiais com forma real, restritos ao diretório temporário de pytest.
    root = tmp_path_factory.mktemp('artificial-complement')
    source = read_jsonl(dataset/'sources.jsonl')[0]
    inputs = [{'id': s['id'], 'text': s['text']} for s in source['sentences']]
    records = []
    for method in ('llm_direct', 'phrase_guided_rewrite'):
        context = {'approval_reference': 'ARTIFICIAL-UNIT-TEST', 'source_phrase': inputs[0]['text'], 'keywords': [inputs[0]['text'].split()[1]]}
        given = inputs if method == 'llm_direct' else inputs[:1]
        spec = session_candidate_spec(method, given, context)
        raw = json.dumps({'sentences': [{'text': r['text'].replace('descreve', 'apresenta'), 'source_sentence_ids': [r['id']]} for r in given]})
        records.append(record_session_candidate(spec, raw, root/'cache', method))
    en = session_candidate_spec('translate_to_en', inputs)
    raw_en = json.dumps({'sentences': [{'text': 'Artificial English fixture sentence ' + str(i) + '.', 'source_sentence_ids': [r['id']]} for i, r in enumerate(inputs)]})
    parent = record_session_candidate(en, raw_en, root/'cache', 'en')
    middle = [{'id': r['source_sentence_ids'][0], 'text': r['text']} for r in parent['structured']['sentences']]
    pt = session_candidate_spec('translate_to_pt', middle, {'parent_cache_key': parent['cache_key']})
    raw_pt = json.dumps({'sentences': [{'text': r['text'].replace('descreve', 'relata'), 'source_sentence_ids': [r['id']]} for r in inputs]})
    records.extend([parent, record_session_candidate(pt, raw_pt, root/'cache', 'pt')])
    result = root/'with-cache'
    add_cached_candidates(dataset, records, result)
    assert {p['synthetic_type'] for p in read_jsonl(result/'pairs.jsonl')} == {f'C{i}' for i in range(8)}
    return result


@pytest.mark.parametrize('corruption', ['parent_missing', 'parent_method', 'parent_source', 'middle_text', 'parent_raw', 'cycle', 'record_id', 'fixture', 'duplicate_input', 'c6_phrase', 'c6_keywords'])
def test_cache_chain_and_c6_negative_controls(llm_dataset, tmp_path, corruption):
    folder = clone_unsealed(llm_dataset, tmp_path)
    pairs = read_jsonl(folder/'pairs.jsonl')
    pair = next(p for p in pairs if p['method'] == ('phrase_guided_rewrite' if corruption.startswith('c6') else 'backtranslation'))
    path = folder/'cache'/f"{pair['generation']['cache_request_id']}.json"
    record = read_json(path)
    parent_path = folder/'cache/en.json'
    parent = read_json(parent_path)
    if corruption == 'parent_missing':
        parent_path.unlink()
    elif corruption in {'parent_method', 'parent_source', 'parent_raw'}:
        if corruption == 'parent_method':
            parent['request']['method'] = 'llm_direct'
        elif corruption == 'parent_source':
            other = next(s for s in read_jsonl(folder/'sources.jsonl') if s['id'] != pair['source_id'])
            parent['request']['input'] = [{'id': s['id'], 'text': s['text']} for s in other['sentences']]
        else:
            parent['raw'] = '{"sentences":[]}'
        parent['cache_key'] = identity(parent['request'])
        record['request']['context']['parent_cache_key'] = parent['cache_key']
        parent_path.write_bytes(canonical(parent))
    elif corruption == 'middle_text':
        record['request']['input'][0]['text'] += ' Divergent intermediate.'
    elif corruption == 'cycle':
        record['request']['context']['parent_cache_key'] = record['cache_key']
    elif corruption == 'record_id':
        record['request_id'] = 'another-record'
    elif corruption == 'fixture':
        record['synthetic_fixture'] = True
    elif corruption == 'duplicate_input':
        record['request']['input'].append(record['request']['input'][0])
    elif corruption == 'c6_phrase':
        record['request']['context']['source_phrase'] = 'Phrase absent from source.'
    else:
        record['request']['context']['keywords'] = ['absent-keyword']
    record['cache_key'] = identity(record['request'])
    pair['generation']['cache_key'] = record['cache_key']
    path.write_bytes(canonical(record))
    for row in pair['sentences']:
        row['parameters'] = deepcopy(pair['generation'])
        row['transformation'] = pair['method']
    replace_jsonl(folder, 'pairs.jsonl', pairs)
    with pytest.raises((ValueError, KeyError, FileNotFoundError)):
        validate_data(folder, sealed=False)


@pytest.fixture(scope='module')
def human_freeze_fixture(llm_dataset, tmp_path_factory):
    import csv
    root = tmp_path_factory.mktemp('artificial-human-review')
    folder = clone_unsealed(llm_dataset, root)
    sources = read_jsonl(folder/'sources.jsonl')
    for s in sources:
        s.update(license_status='source_verified', exposure='not_used_for_development')
    replace_jsonl(folder, 'sources.jsonl', sources)
    config = read_json(folder/'config.json')
    config.update(purpose='experimental_candidate', scientific_approval=True, approval_reference='ARTIFICIAL-UNIT-ONLY')
    (folder/'config.json').write_bytes(canonical(config))
    seal(folder, {'purpose': 'experimental_candidate'})
    formatted = root/'formatted'
    add_formats(folder, formatted, 1)
    package = root/'package'
    prepare_review(formatted, package, 7)
    columns = ['id', 'decision', 'reason', 'observation', 'reviewer', 'date']
    response_path = root/'ARTIFICIAL-responses.csv'
    with response_path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({'id': i['id'], 'decision': 'accept', 'reason': 'ARTIFICIAL pytest response, no human review', 'observation': '', 'reviewer': 'ARTIFICIAL-fixture', 'date': '2026-10-24'} for i in read_jsonl(package/'items.jsonl'))
    imported = root/'imported'
    import_review(package, response_path, imported)
    auth = {'approved': True, 'reference': 'ARTIFICIAL-UNIT-ONLY', 'review_scope_accepted': True,
            'source_alerts_resolved': True, 'cache_verified': True, 'reproduction_verified': True}
    return formatted, imported, auth


def test_positive_artificial_review_freeze_export_import(human_freeze_fixture, tmp_path):
    from hts_core.adapters.dataset_store import export_bundle, import_bundle
    folder, review, auth = human_freeze_fixture
    result = freeze(folder, review, auth, tmp_path/'frozen')
    assert result['metadata']['semantic_training_ready'] is False
    assert validate_data(tmp_path/'frozen')['pairs'] > 0
    export_bundle(tmp_path/'frozen', tmp_path/'data.zip')
    imported = import_bundle(tmp_path/'data.zip', tmp_path/'restored')
    assert imported['version'] == result['version']
    assert imported['metadata']['purpose'] == 'frozen_derivation_candidate'


@pytest.mark.parametrize('corruption', ['unknown_id', 'duplicate', 'missing', 'extra', 'version', 'text', 'selection', 'reason', 'date', 'modality', 'reject', 'ambiguous', 'authorization', 'license', 'exposure', 'reproduction', 'purpose'])
def test_freeze_revalidates_reviews_and_preconditions(human_freeze_fixture, tmp_path, corruption):
    original, imported, auth = human_freeze_fixture
    auth = deepcopy(auth)
    folder = clone_unsealed(original, tmp_path)
    review = read_json(imported/'review.json')
    if corruption == 'unknown_id':
        review['responses'][0]['id'] = 'does-not-exist'
    elif corruption == 'duplicate':
        review['responses'].append(review['responses'][0])
    elif corruption == 'missing':
        review['responses'].pop()
    elif corruption == 'extra':
        review['responses'].append({**review['responses'][0], 'id': 'extra'})
    elif corruption == 'version':
        review['dataset_version'] = 'wrong-version'
    elif corruption == 'text':
        review['items'][0]['transformed_text'] += ' Changed.'
    elif corruption == 'selection':
        review['selection']['sampled'] = review['selection']['sampled'][:1]
    elif corruption in {'reason', 'date'}:
        review['responses'][0][corruption] = ''
    elif corruption == 'modality':
        review['modality'] = 'human_independent'
    elif corruption in {'reject', 'ambiguous'}:
        review['responses'][0]['decision'] = corruption
    elif corruption == 'authorization':
        auth['review_scope_accepted'] = False
    elif corruption in {'license', 'exposure'}:
        sources = read_jsonl(folder/'sources.jsonl')
        chosen = next(s for s in sources if s['split'] == 'test')
        chosen['license_status' if corruption == 'license' else 'exposure'] = 'historical_declared' if corruption == 'license' else 'development_refcorpus'
        replace_jsonl(folder, 'sources.jsonl', sources)
    elif corruption == 'reproduction':
        auth['reproduction_verified'] = False
    else:
        config = read_json(folder/'config.json')
        config['purpose'] = 'pilot'
        (folder/'config.json').write_bytes(canonical(config))
    manifest = seal(folder, {'purpose': read_json(folder/'config.json')['purpose']})
    import csv
    import io
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=['id', 'decision', 'reason', 'observation', 'reviewer', 'date'])
    writer.writeheader()
    writer.writerows(review['responses'])
    review['source_responses_text'] = stream.getvalue()
    review['source_responses_sha256'] = digest(stream.getvalue().encode('utf-8'))
    review['identity'] = identity({k: v for k, v in review.items() if k != 'identity'})
    write_json(tmp_path/'review/review.json', review)
    with pytest.raises((ValueError, PermissionError)):
        freeze(folder, tmp_path/'review', auth, tmp_path/'must-not-freeze')


@pytest.mark.parametrize('corruption', ['canonical_input', 'output_ancestry', 'raw', 'pair_method'])
def test_cache_reconstructs_canonical_contract(llm_dataset, tmp_path, corruption):
    folder = clone_unsealed(llm_dataset, tmp_path)
    pairs = read_jsonl(folder/'pairs.jsonl')
    pair = next(p for p in pairs if p['method'] == 'llm_direct')
    path = folder/'cache'/f"{pair['generation']['cache_request_id']}.json"
    record = read_json(path)
    if corruption == 'canonical_input':
        record['request']['input'][0]['text'] = 'Uma entrada diferente da fonte canônica.'
        record['cache_key'] = identity(record['request'])
        pair['generation']['cache_key'] = record['cache_key']
    elif corruption == 'output_ancestry':
        rows = record['structured']['sentences']
        rows[0]['source_sentence_ids'], rows[1]['source_sentence_ids'] = rows[1]['source_sentence_ids'], rows[0]['source_sentence_ids']
        record['raw'] = json.dumps(record['structured'])
    elif corruption == 'raw':
        record['raw'] = '{"sentences":[]}'
    else:
        pair['method'] = 'backtranslation'
    path.write_bytes(canonical(record))
    for row in pair['sentences']:
        row['parameters'] = deepcopy(pair['generation'])
        row['transformation'] = pair['method']
    replace_jsonl(folder, 'pairs.jsonl', pairs)
    with pytest.raises(ValueError):
        validate_data(folder, sealed=False)


def test_freeze_rejects_self_hashed_orphan_accept(llm_dataset, tmp_path):
    folder = clone_unsealed(llm_dataset, tmp_path)
    sources = read_jsonl(folder/'sources.jsonl')
    for s in sources:
        s.update(license_status='source_verified', exposure='not_used_for_development')
    replace_jsonl(folder, 'sources.jsonl', sources)
    config = read_json(folder/'config.json')
    config['purpose'] = 'experimental_candidate'
    (folder/'config.json').write_bytes(canonical(config))
    seal(folder, {'purpose': 'experimental_candidate'})
    formatted = tmp_path/'formatted'
    manifest = add_formats(folder, formatted, 1)
    review = tmp_path/'forged-review'
    body = {'dataset_version': manifest['version'], 'responses': [{'id': 'ID-DOES-NOT-EXIST', 'decision': 'accept'}]}
    write_json(review/'review.json', {**body, 'identity': identity(body)})
    authorization = {'approved': True, 'reference': 'ARTIFICIAL-TEST-NOT-HUMAN', 'review_scope_accepted': True,
                     'source_alerts_resolved': True, 'cache_verified': True, 'reproduction_verified': True}
    with pytest.raises(ValueError):
        freeze(formatted, review, authorization, tmp_path/'must-not-freeze')


class MemoryCollection:
    def __init__(self):
        self.rows = {}
        self.fail_after: int | None = None

    def find_one(self, query):
        return next((deepcopy(r) for r in self.rows.values() if all(r.get(k) == v for k, v in query.items())), None)

    def update_one(self, query, update, upsert=False):
        if self.fail_after == 0:
            raise OSError('ARTIFICIAL storage interruption')
        if self.fail_after is not None:
            self.fail_after -= 1
        row = self.find_one(query)
        if row is None:
            if not upsert:
                return
            row = deepcopy(update.get('$setOnInsert', query))
        row.update(deepcopy(update.get('$set', {})))
        self.rows[row['_id']] = row

    def find(self, query):
        return [deepcopy(r) for r in self.rows.values() if all(r.get(k) == v for k, v in query.items())]

    def count_documents(self, query):
        return len(self.find(query))


def test_pdf_preserves_literal_cjk_and_greek():
    from hts_core.adapters.dataset_formats import render
    from hts_core.adapters.parsers import parse_document
    text = 'O rio 長江 também se escreve 长江. Origâmi: 折り紙. Marioneta: 人形浄瑠璃 e 文楽. Archaea: ἀρχαῖος.'
    data, metadata = render(text, 'pdf')
    assert parse_document('unicode.pdf', data) == text
    assert metadata['fallback_sha256'] == '568d44ed35df4ffdd53ce99dab039b2c0b60c291847574e9b46f50415c47ce7b'
    assert render(text, 'pdf')[0] == data


def test_zero_effect_permutation_rejected_even_with_nonidentity_indices():
    from hts_core.adapters.dataset_validation import _check_transformation
    text = 'Uma sentença repetida de origem conhecida.'
    original = [{'id': 'a', 'text': text}, {'id': 'b', 'text': text}]
    sources = {'A': {'sentences': original}}
    origins = {r['id']: ('A', r) for r in original}
    pair = {'synthetic_type': 'C7', 'method': 'reorder', 'severity': 'permutation', 'source_id': 'A', 'text': text + ' ' + text,
            'generation': {'permutation': [1, 0]}, 'sentences': [
                {'text': text, 'ancestors': [{'source_id': 'A', 'sentence_id': sid}]} for sid in ('b', 'a')]}
    with pytest.raises(ValueError, match='sem efeito'):
        _check_transformation(pair, sources, origins, {})


def test_zero_effect_character_operation_rejected():
    from hts_core.adapters.dataset_validation import _check_transformation
    text = 'ABC DEFG HIJK LMNO.'
    pair = {'synthetic_type': 'C2', 'method': 'character_substitution', 'severity': '0.05', 'source_id': 'A',
            'generation': {'requested_rate': .05, 'semantic_preservation': 'unverified', 'by_sentence': [{
                'source_sentence_id': 'a', 'operations': [], 'eligible': 0, 'realized_count': 0, 'realized_rate': 0,
                'requested_rate': .05, 'effective_levenshtein': 0}]},
            'sentences': [{'text': text, 'ancestors': [{'source_id': 'A', 'sentence_id': 'a'}]}]}
    with pytest.raises(ValueError, match='sem efeito'):
        _check_transformation(pair, {}, {'a': ('A', {'text': text})}, {'edit_rates': [.05]})


class MemoryDatabase:
    name = 'hts_dataset_ARTIFICIAL_pytest'

    def __init__(self):
        self.datasets, self.dataset_pairs = MemoryCollection(), MemoryCollection()


@pytest.mark.parametrize('corruption', ['body', 'declared_hash', 'manifest_body', 'extra_pair'])
def test_mongo_checks_stored_content_not_just_declared_hash(llm_dataset, corruption):
    from hts_core.adapters.dataset_mongo import import_version
    db = MemoryDatabase()
    first = import_version(llm_dataset, db)
    assert import_version(llm_dataset, db) == first
    version = first['version']
    if corruption == 'manifest_body':
        db.datasets.rows[version]['manifest']['metadata']['purpose'] = 'fabricated'
    elif corruption == 'extra_pair':
        existing = deepcopy(next(iter(db.dataset_pairs.rows.values())))
        existing['_id'] = 'unexpected-extra'
        db.dataset_pairs.rows[existing['_id']] = existing
    else:
        row = next(iter(db.dataset_pairs.rows.values()))
        if corruption == 'body':
            row['pair']['text'] += ' Content tampered without changing declared hash.'
        else:
            row['sha256'] = 'wrong'
    with pytest.raises(ValueError):
        import_version(llm_dataset, db)
    assert db.datasets.rows[version]['state'] == 'integrity_conflict'


def test_mongo_partial_failure_resumes_without_deleting(llm_dataset):
    from hts_core.adapters.dataset_mongo import import_version
    db = MemoryDatabase()
    db.dataset_pairs.fail_after = 3
    with pytest.raises(OSError):
        import_version(llm_dataset, db)
    assert len(db.dataset_pairs.rows) == 3
    assert next(iter(db.datasets.rows.values()))['state'] == 'importing'
    preserved = deepcopy(db.dataset_pairs.rows)
    db.dataset_pairs.fail_after = None
    result = import_version(llm_dataset, db)
    assert result['status'] == 'complete'
    assert all(db.dataset_pairs.rows[k] == v for k, v in preserved.items())
    assert result['pairs'] == len(read_jsonl(llm_dataset/'pairs.jsonl'))


@pytest.fixture(scope='module')
def idf_fixture(dataset, tmp_path_factory):
    from hts_core.application.dataset_pipeline import build_training_idf
    path = tmp_path_factory.mktemp('idf-descriptor')/'idf'
    build_training_idf(dataset, path)
    return path


@pytest.mark.parametrize('corruption', ['revision', 'raw_hash', 'input', 'allowed_split', 'config', 'pipeline', 'table', 'formula', 'purpose', 'execution_version', 'execution_hash', 'execution_date'])
def test_idf_reconstructs_descriptor_even_after_rehash(dataset, idf_fixture, tmp_path, corruption):
    from hts_core.adapters.dataset_validation import validate_training_idf
    descriptor, table = read_json(idf_fixture/'construction.json'), read_json(idf_fixture/'idf.json')
    execution = read_json(idf_fixture/'execution.json')
    if corruption == 'revision':
        descriptor['training_sources'][0]['revision'] += 1
    elif corruption == 'raw_hash':
        descriptor['training_sources'][0]['raw_sha256'] = 'fake'
    elif corruption == 'input':
        descriptor['input_identity'] = 'fake'
    elif corruption == 'allowed_split':
        descriptor['allowed_split'] = 'test'
    elif corruption == 'config':
        descriptor['config']['seed'] += 1
    elif corruption == 'pipeline':
        descriptor['pipeline']['model'] = {'fake': True}
    elif corruption == 'table':
        table['df'][next(iter(table['df']))] += 1
    elif corruption == 'purpose':
        descriptor['purpose'] = 'wrong'
    elif corruption == 'formula':
        table['formula'] = 'wrong'
    elif corruption == 'execution_version':
        execution['dataset_version'] = 'wrong'
    elif corruption == 'execution_hash':
        execution['serialized_table_sha256'] = 'wrong'
    else:
        execution['constructed_utc'] = 'invalid-date'
    descriptor['table_content_sha256'] = identity({k: v for k, v in table.items() if k != 'version'})
    table['version'] = descriptor['identity'] = identity({k: v for k, v in descriptor.items() if k != 'identity'})
    write_json(tmp_path/'idf.json', table)
    write_json(tmp_path/'construction.json', descriptor)
    write_json(tmp_path/'execution.json', execution)
    with pytest.raises(ValueError):
        validate_training_idf(dataset, tmp_path)
