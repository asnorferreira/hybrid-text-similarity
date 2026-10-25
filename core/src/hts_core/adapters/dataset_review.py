import csv
import io
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from datetime import datetime

from hts_core.adapters.dataset_store import canonical, digest, identity, read_json, read_jsonl, seal, verify_seal, write_json, write_jsonl, write_new
from hts_core.adapters.dataset_validation import validate_data
from hts_core.domain.dataset import ranked


def prepare_review(folder, destination, seed, sample_percent=20, pilot_count=None):
    if not 0 < sample_percent <= 100:
        raise ValueError('percentual de revisão inválido')
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    validate_data(folder)
    destination.mkdir(parents=True, exist_ok=False)
    sources = {s['id']: s for s in read_jsonl(folder/'sources.jsonl')}
    pairs = read_jsonl(folder/'pairs.jsonl')
    strata = defaultdict(list)
    for p in pairs:
        strata[(p['split'], p['synthetic_type'], p['method'], p['severity'])].append(p['id'])
    selected, directed = set(), set()
    for stratum, ids in sorted(strata.items()):
        if stratum[1] in {'C5', 'C6'} or stratum[2] == 'negative_hard':
            directed.update(ids)
        else:
            count = max(1, (len(ids) * sample_percent + 99) // 100)
            selected.update(ranked(ids, seed, ':'.join(stratum))[:count])
    if pilot_count is not None:
        if manifest['metadata']['purpose'] != 'pilot' or pilot_count < 1:
            raise ValueError('limite de itens só se aplica ao piloto autorizado')
        chosen = []
        for kind in ('C5', 'C6', 'C0', 'C2', 'C1', 'C3', 'C4', 'C7'):
            options = [p['id'] for p in pairs if p['synthetic_type'] == kind]
            if options and len(chosen) < pilot_count:
                chosen.append(ranked(options, seed, 'pilot-review-' + kind)[0])
        remaining = ranked({p['id'] for p in pairs} - set(chosen), seed, 'pilot-review-fill')
        chosen += remaining[:max(0, pilot_count - len(chosen))]
        selected, directed = set(chosen), set()
    items = []
    for p in sorted(pairs, key=lambda p: p['id']):
        if p['id'] not in selected | directed:
            continue
        items.append({'id': p['id'], 'source_id': p['source_id'], 'split': p['split'], 'synthetic_type': p['synthetic_type'], 'method': p['method'],
                      'severity': p['severity'], 'selection': 'pilot_class_coverage_hash_sample' if pilot_count is not None else 'directed' if p['id'] in directed else 'stratified_hash_sample',
                      'source_texts': [{'source_id': sid, 'text': ' '.join(s['text'] for s in sources[sid]['sentences'])} for sid in p['source_ids']],
                      'transformed_text': p['text'], 'operations': p['generation'],
                      'criteria': 'sentido, fatos novos, negação, números/unidades, entidades, omissões, fluência e sobreposição em negativos',
                      'decision': '', 'reason': '', 'observation': '', 'reviewer': '', 'date': ''})
    write_jsonl(destination/'items.jsonl', items)
    panels = []
    for item in items:
        originals = ''.join('<h3>' + ('Fonte focal: ' if s['source_id'] == item['source_id'] else 'Outra origem da composição: ')
                            + escape(s['source_id']) + '</h3><p>' + escape(s['text']) + '</p>' for s in item['source_texts'])
        panels.append('<details><summary>' + escape(item['id']) + ' — ' + escape(item['method']) + ' / ' + escape(item['severity'])
                      + '</summary><p>Split: ' + escape(item['split']) + '; seleção: ' + escape(item['selection'])
                      + '</p><div class="pair"><section><h2>Fontes</h2>' + originals + '</section><section><h2>Transformado</h2><p>'
                      + escape(item['transformed_text']) + '</p></section></div><h3>Operações</h3><pre>'
                      + escape(canonical(item['operations']).decode()) + '</pre><p>Resposta em branco em responses.csv.</p></details>')
    html = ('<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
            '<title>Revisão individual pendente</title><style>body{font:16px system-ui;margin:2rem;line-height:1.5}'
            '.pair{display:flex;gap:2rem}.pair section{flex:1;min-width:0}details{border:1px solid #aaa;padding:1rem;margin:1rem 0}'
            'summary,pre{overflow-wrap:anywhere;white-space:pre-wrap}@media(max-width:800px){.pair{display:block}}</style>'
            '<h1>Revisão individual pendente</h1><p>Finalidade: ' + escape(manifest['metadata']['purpose'])
            + '. Neste piloto, train/validation/test são divisões de desenvolvimento, fora do teste experimental final.</p>'
            '<p>Compare a fonte focal e o candidato; outras origens explicam a composição. Preencha responses.csv, sem copiar notas do sistema. '
            'Confira fatos novos, negação, números/unidades, entidades, omissões, coerência e sobreposição nos negativos. '
            'Accept/reject/ambiguous são decisões suas; operação conhecida não certifica sentido. Um revisor: sem κ.</p>'
            + ''.join(panels) + '</html>')
    write_new(destination/'revisao.html', html.encode('utf-8'))
    columns = ['id', 'decision', 'reason', 'observation', 'reviewer', 'date']
    with (destination/'responses.csv').open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: item[k] for k in columns} for item in items)
    write_json(destination/'selection.json', {'dataset_version': manifest['version'], 'seed': seed, 'percent': sample_percent,
                                             'strata': {':'.join(k): len(v) for k, v in sorted(strata.items())},
                                             'directed': sorted(directed), 'sampled': sorted(selected), 'reviewers': 1,
                                             'pilot_count': pilot_count,
                                             'status': 'pending', 'limits': 'sample review does not certify all items; no Cohen kappa with one reviewer'})
    instructions = ('Revisão individual PENDENTE. Abra items.jsonl para ler cada fonte e transformação; preencha somente responses.csv.\n'
                    'decision: accept, reject ou ambiguous; motivo, responsável e data ISO obrigatórios. Não há predições/escores.\n'
                    'Confira fatos, negações, números, unidades, entidades, omissões, coerência e coincidências indevidas em negativos.\n'
                    'Operação conhecida não comprova sentido. Não aceite paráfrase só por fluência. Use ambiguous quando não souber.\n'
                    'Não apague exemplos rejeitados. Importe respostas para pasta nova; registre novas tentativas sem substituir as anteriores.\n'
                    'A revisão amostral tem alcance limitado aos itens inspecionados; não calcular kappa com um revisor.\n'
                    'No piloto de 8 itens, anote tempo real de início/fim; o tamanho da revisão experimental ainda não foi confirmado.\n')
    write_new(destination/'LEIA-ME.txt', instructions.encode('utf-8'))
    seal(destination, {'purpose': 'review_package', 'dataset_version': manifest['version'], 'modality': 'human_individual'})
    return {'items': len(items), 'directed': len(directed), 'sampled': len(selected), 'status': 'human_pending'}


def import_review(package, responses, destination):
    package, destination = Path(package), Path(destination)
    package_manifest = verify_seal(package)
    selection = read_json(package/'selection.json')
    items = {r['id']: r for r in read_jsonl(package/'items.jsonl')}
    with Path(responses).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len({r['id'] for r in rows}) != len(rows) or set(r['id'] for r in rows) != set(items):
        raise ValueError('respostas duplicadas/órfãs/ausentes')
    from datetime import datetime
    for row in rows:
        if row['decision'] not in {'accept', 'reject', 'ambiguous'} or not all(row.get(k, '').strip() for k in ('reason', 'reviewer', 'date')):
            raise ValueError('revisão incompleta; respostas humanas não preenchidas')
        datetime.fromisoformat(row['date'])
    destination.mkdir(parents=True, exist_ok=False)
    body = {'selection': selection, 'items_sha256': digest((package/'items.jsonl').read_bytes()), 'items': list(items.values()),
            'responses': rows, 'source_responses_sha256': digest(Path(responses).read_bytes()),
            'source_responses_text': Path(responses).read_bytes().decode('utf-8'),
            'kind': 'individual_self_report_no_identity_attestation', 'dataset_version': selection['dataset_version'],
            'modality': 'human_individual', 'package_manifest': package_manifest}
    validate_review(body)
    write_json(destination/'review.json', {**body, 'identity': identity(body)})
    return {'responses': len(rows), 'accepted': sum(r['decision'] == 'accept' for r in rows), 'status': 'imported_individual_review'}


def review_item(pair, sources):
    return {'id': pair['id'], 'source_id': pair['source_id'], 'split': pair['split'], 'synthetic_type': pair['synthetic_type'],
            'method': pair['method'], 'severity': pair['severity'], 'source_texts': [
                {'source_id': sid, 'text': ' '.join(r['text'] for r in sources[sid]['sentences'])} for sid in pair['source_ids']],
            'transformed_text': pair['text'], 'operations': pair['generation']}


def operational_review_ids(pairs):
    chosen = {p['id'] for p in pairs if p['synthetic_type'] in {'C5', 'C6'}}
    strata = {(p['split'], p['method'], p['severity']) for p in pairs if p['synthetic_type'] not in {'C5', 'C6'}}
    for stratum in sorted(strata):
        chosen.add(min(p['id'] for p in pairs if (p['split'], p['method'], p['severity']) == stratum))
    return sorted(chosen)


def human_review_ids(pairs, selection):
    if selection.get('pilot_count') is not None:
        raise ValueError('amostra piloto não aprova dataset experimental')
    percent = selection['percent']
    if type(percent) is not int or not 0 < percent <= 100:
        raise ValueError('política de amostragem inválida')
    strata = defaultdict(list)
    for p in pairs:
        strata[(p['split'], p['synthetic_type'], p['method'], p['severity'])].append(p['id'])
    chosen = set()
    for stratum, ids in sorted(strata.items()):
        if stratum[1] in {'C5', 'C6'} or stratum[2] == 'negative_hard':
            chosen.update(ids)
        else:
            count = max(1, (len(ids) * percent + 99) // 100)
            chosen.update(ranked(ids, selection['seed'], ':'.join(stratum))[:count])
    return sorted(chosen)


def prepare_automated_review(folder, destination):
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    validate_data(folder)
    sources = {s['id']: s for s in read_jsonl(folder/'sources.jsonl')}
    pairs = {p['id']: p for p in read_jsonl(folder/'pairs.jsonl')}
    chosen = operational_review_ids(list(pairs.values()))
    items = [review_item(pairs[pid], sources) for pid in chosen]
    destination.mkdir(parents=True, exist_ok=False)
    write_jsonl(destination/'items.jsonl', items)
    selection = {'dataset_version': manifest['version'], 'policy': 'all_generated_plus_first_id_per_split_method_severity_v1',
                 'expected_ids': chosen, 'modality': 'automated_ai', 'human_review': 'not_performed'}
    write_json(destination/'selection.json', selection)
    write_new(destination/'prompt.txt', (
        'Compare os textos e operações de cada item. Avalie fatos acrescentados/omitidos, negações, números/unidades/datas, '
        'entidades, causalidade/tempo/generalização/contradição, fluência, coerência, cumprimento da transformação e '
        'sobreposição em negativos. Cite fonte e saída em problemas localizados. Accept significa adequação operacional '
        'à derivação/robustez; não certifica equivalência semântica. C2 intensa pode perder sentido; C6 não ganha classe '
        'semântica. Use reject/ambiguous quando necessário. Identifique a dependência: mesmo agente gerador, sem '
        'revisor humano ou independente. Não produza nota semântica contínua.').encode())
    return seal(destination, {'purpose': 'review_package', 'dataset_version': manifest['version'], 'modality': 'automated_ai'})


def import_automated_review(package, responses, destination):
    package, destination = Path(package), Path(destination)
    manifest = verify_seal(package)
    selection = read_json(package/'selection.json')
    items = read_jsonl(package/'items.jsonl')
    rows = read_jsonl(responses)
    body = {'selection': selection, 'items': items, 'items_sha256': digest((package/'items.jsonl').read_bytes()),
            'responses': rows, 'source_responses_sha256': digest(Path(responses).read_bytes()),
            'source_responses_text': Path(responses).read_bytes().decode('utf-8'),
            'kind': 'ai_assessment_not_human_not_independent', 'modality': 'automated_ai',
            'dataset_version': selection['dataset_version'], 'package_manifest': manifest}
    validate_review(body)
    destination.mkdir(parents=True, exist_ok=False)
    write_json(destination/'review.json', {**body, 'identity': identity(body)})
    return {'responses': len(rows), 'modality': 'automated_ai', 'human_review': 'not_performed'}


def validate_review(review, folder=None, dataset_version=None):
    required = {'selection', 'items', 'items_sha256', 'responses', 'source_responses_sha256', 'source_responses_text', 'kind', 'modality', 'dataset_version', 'package_manifest'}
    if set(review) - {'identity'} != required:
        raise ValueError('schema da revisão incompleto/desconhecido')
    if 'identity' in review and review['identity'] != identity({k: v for k, v in review.items() if k != 'identity'}):
        raise ValueError('identidade da revisão divergente')
    modality, selection, items = review['modality'], review['selection'], review['items']
    if modality not in {'human_individual', 'automated_ai'}:
        raise ValueError('modalidade de revisão incompatível; independente não implementada/atestada')
    kind = 'ai_assessment_not_human_not_independent' if modality == 'automated_ai' else 'individual_self_report_no_identity_attestation'
    if review['kind'] != kind:
        raise ValueError('natureza/modalidade da revisão divergente')
    manifest = review['package_manifest']
    manifest_body = {k: manifest[k] for k in ('schema', 'metadata', 'files')}
    if manifest['version'] != identity(manifest_body) or manifest['metadata']['modality'] != modality:
        raise ValueError('manifesto/modalidade do pacote divergente')
    if selection['dataset_version'] != review['dataset_version'] or manifest['metadata']['dataset_version'] != review['dataset_version']:
        raise ValueError('versão da seleção divergente')
    item_bytes = b''.join(canonical(item) for item in items)
    if digest(item_bytes) != review['items_sha256'] or manifest['files']['items.jsonl'] != digest(item_bytes) or manifest['files']['selection.json'] != identity(selection):
        raise ValueError('integridade dos itens/seleção divergente')
    ids = [r['id'] for r in items]
    expected = selection['expected_ids'] if modality == 'automated_ai' else selection['sampled'] + selection['directed']
    if not ids or len(ids) != len(set(ids)) or len(expected) != len(set(expected)) or set(ids) != set(expected):
        raise ValueError('itens duplicados/seleção incompleta')
    rows = review['responses']
    raw = review['source_responses_text']
    if digest(raw.encode('utf-8')) != review['source_responses_sha256']:
        raise ValueError('respostas originais/hash divergentes')
    parsed = [json.loads(line) for line in raw.splitlines() if line] if modality == 'automated_ai' else list(csv.DictReader(io.StringIO(raw.lstrip('\ufeff'))))
    if parsed != rows:
        raise ValueError('respostas originais divergem das importadas')
    row_ids = [r['id'] for r in rows]
    if len(row_ids) != len(set(row_ids)) or set(row_ids) != set(ids):
        raise ValueError('respostas duplicadas/órfãs/ausentes/extras')
    for row in rows:
        fields = {'id', 'decision', 'reason', 'observation', 'reviewer', 'date'} if modality == 'human_individual' else {
            'id', 'decision', 'reason', 'date', 'procedure', 'interface', 'model_revision', 'prompt_sha256', 'item_sha256',
            'generator_relation', 'limitations', 'findings'}
        if set(row) != fields or row['decision'] not in {'accept', 'reject', 'ambiguous', 'not_evaluable'} or not row['reason'].strip():
            raise ValueError('campos/decisão da revisão inválidos')
        datetime.fromisoformat(row['date'])
        if modality == 'human_individual' and not row['reviewer'].strip():
            raise ValueError('responsável ausente; nome não atesta identidade')
        if modality == 'automated_ai':
            item = next(i for i in items if i['id'] == row['id'])
            if row['item_sha256'] != identity(item) or row['prompt_sha256'] != manifest['files']['prompt.txt']:
                raise ValueError('avaliação vinculada a outro texto/prompt')
            if not all(row[k] for k in ('procedure', 'interface', 'generator_relation', 'limitations')) or not isinstance(row['findings'], list):
                raise ValueError('alcance/procedimento/limitações da IA ausentes')
    if folder is not None:
        manifest = verify_seal(folder)
        if review['dataset_version'] != (dataset_version or manifest['version']):
            raise ValueError('revisão de outra versão')
        sources = {s['id']: s for s in read_jsonl(Path(folder)/'sources.jsonl')}
        pairs = {p['id']: p for p in read_jsonl(Path(folder)/'pairs.jsonl')}
        for item in items:
            if item['id'] not in pairs:
                raise ValueError('ID revisado inexistente')
            actual = review_item(pairs[item['id']], sources)
            if any(item.get(k) != v for k, v in actual.items()):
                raise ValueError('texto/operação/fonte revisados divergentes')
        if modality == 'automated_ai' and (selection.get('policy') != 'all_generated_plus_first_id_per_split_method_severity_v1' or sorted(ids) != operational_review_ids(list(pairs.values()))):
            raise ValueError('cobertura de avaliação automatizada incompleta')
        if modality == 'human_individual' and sorted(ids) != human_review_ids(list(pairs.values()), selection):
            raise ValueError('cobertura da amostra humana incompleta')
    return review


def freeze(folder, review_folder, authorization, destination):
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    config = read_json(folder/'config.json')
    operational = config['purpose'] == 'operational_derivation'
    if config['purpose'] not in {'experimental_candidate', 'operational_derivation'} or not authorization.get('approved') or not authorization.get('reference'):
        raise PermissionError('piloto/contrato não aprovado não pode ser congelado como dataset experimental')
    expected_types = set(config.get('required_types', [f'C{i}' for i in range(8)]))
    if set(p['synthetic_type'] for p in read_jsonl(folder/'pairs.jsonl')) != expected_types:
        raise ValueError('cobertura C0–C7 incompleta')
    sources = read_jsonl(folder/'sources.jsonl')
    if any(s['license_status'] != 'source_verified' or (s['split'] == 'test' and s['exposure'] != ('construction_inspected_no_predictive_use' if operational else 'not_used_for_development')) for s in sources):
        raise ValueError('licença/exposição das fontes não resolvida')
    review = read_json(Path(review_folder)/'review.json')
    validate_review(review, folder)
    if operational and (review['modality'] != 'automated_ai' or authorization.get('purpose') != 'operational_derivation' or config.get('review_policy') != 'all_generated_plus_first_id_per_split_method_severity_v1'):
        raise ValueError('modalidade/política/finalidade operacional incompatível')
    if not operational and review['modality'] != 'human_individual':
        raise ValueError('aprovação científica não é suprida por avaliação automatizada')
    if review['identity'] != identity({k: v for k, v in review.items() if k != 'identity'}):
        raise ValueError('identidade da revisão divergente')
    if review['dataset_version'] != manifest['version'] or not review['responses'] or any(r['decision'] != 'accept' for r in review['responses']):
        raise ValueError('revisão ausente/divergente/rejeitada/ambígua; preservar versão e tratar exclusões')
    if not authorization.get('review_scope_accepted') or not authorization.get('source_alerts_resolved'):
        raise PermissionError('alcance da revisão e alertas exigem decisão explícita')
    if not authorization.get('cache_verified') or not authorization.get('reproduction_verified'):
        raise PermissionError('cache/reprodução ainda não verificados')
    if operational:
        from hts_core.adapters.dataset_operational import verify_operational_requirements
        verify_operational_requirements(folder, authorization)
    report = validate_data(folder)
    if report['formats'] == 0:
        raise ValueError('formatos não verificados')
    destination.mkdir(parents=True, exist_ok=False)
    for name in manifest['files']:
        if name != 'pairs.jsonl' or config.get('record_contract') != 'assessment_v2':
            write_new(destination/name, (folder/name).read_bytes())
    if config.get('record_contract') == 'assessment_v2':
        write_new(destination/'construction-pairs.jsonl', (folder/'pairs.jsonl').read_bytes())
        pairs = read_jsonl(folder/'pairs.jsonl')
        for pair in pairs:
            pair['content_assessment'] = assessment_state(pair['id'], review)
        write_jsonl(destination/'pairs.jsonl', pairs)
    write_json(destination/'freeze-authorization.json', authorization)
    write_json(destination/'review.json', review)
    return seal(destination, {'purpose': 'frozen_operational_derivation' if operational else 'frozen_derivation_candidate',
                              'parent_version': manifest['version'], 'assessment_modality': review['modality'],
                              'human_review': 'not_performed' if operational else 'individual_self_report',
                              'semantic_training_ready': False, 'semantic_target': 'pending'})


def assessment_state(pair_id, review=None):
    state = {'status': 'not_assessed', 'scope': 'whole_pair_not_individual_sentences',
             'modality': None, 'review_identity': None, 'review_dataset_version': None, 'response_id': None}
    if review is not None:
        response = next((r for r in review['responses'] if r['id'] == pair_id), None)
        if response is not None:
            state.update(status=response['decision'], modality=review['modality'], review_identity=review['identity'],
                         review_dataset_version=review['dataset_version'], response_id=pair_id)
    return state
