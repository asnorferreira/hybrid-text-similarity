import csv
from collections import defaultdict
from html import escape
from pathlib import Path

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
    return {'items': len(items), 'directed': len(directed), 'sampled': len(selected), 'status': 'human_pending'}


def import_review(package, responses, destination):
    package, destination = Path(package), Path(destination)
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
            'kind': 'individual_self_report_no_identity_attestation', 'dataset_version': selection['dataset_version']}
    write_json(destination/'review.json', {**body, 'identity': identity(body)})
    return {'responses': len(rows), 'accepted': sum(r['decision'] == 'accept' for r in rows), 'status': 'imported_individual_review'}


def freeze(folder, review_folder, authorization, destination):
    folder, destination = Path(folder), Path(destination)
    manifest = verify_seal(folder)
    report = validate_data(folder)
    config = read_json(folder/'config.json')
    if config['purpose'] != 'experimental_candidate' or not authorization.get('approved') or not authorization.get('reference'):
        raise PermissionError('piloto/contrato não aprovado não pode ser congelado como dataset experimental')
    if set(p['synthetic_type'] for p in read_jsonl(folder/'pairs.jsonl')) != set(f'C{i}' for i in range(8)):
        raise ValueError('cobertura C0–C7 incompleta')
    sources = read_jsonl(folder/'sources.jsonl')
    if any(s['license_status'] != 'source_verified' or (s['split'] == 'test' and s['exposure'] != 'not_used_for_development') for s in sources):
        raise ValueError('licença/exposição das fontes não resolvida')
    review = read_json(Path(review_folder)/'review.json')
    if review['identity'] != identity({k: v for k, v in review.items() if k != 'identity'}):
        raise ValueError('identidade da revisão divergente')
    if review['dataset_version'] != manifest['version'] or not review['responses'] or any(r['decision'] != 'accept' for r in review['responses']):
        raise ValueError('revisão ausente/divergente/rejeitada/ambígua; preservar versão e tratar exclusões')
    if not authorization.get('review_scope_accepted') or not authorization.get('source_alerts_resolved'):
        raise PermissionError('alcance da revisão e alertas exigem decisão explícita')
    if report['formats'] == 0:
        raise ValueError('formatos não verificados')
    if not authorization.get('cache_verified') or not authorization.get('reproduction_verified'):
        raise PermissionError('cache/reprodução ainda não verificados')
    destination.mkdir(parents=True, exist_ok=False)
    for name in manifest['files']:
        write_new(destination/name, (folder/name).read_bytes())
    write_json(destination/'freeze-authorization.json', authorization)
    write_json(destination/'review.json', review)
    return seal(destination, {'purpose': 'frozen_derivation_candidate', 'parent_version': manifest['version'],
                              'semantic_training_ready': False, 'semantic_target': 'pending'})
