from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import zipfile

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import inspect_dataset, save_json_new
from hts_core.adapters.training_contract import validate_s5b
from hts_core.domain.human_reference import agreement_and_consensus, fields, nonempty, validate_judgment


CORE = Path(__file__).resolve().parents[3]
HUMAN_PLAN_SCHEMA = 'hts-s5c-human-plan-1'
HUMAN_DEFAULTS = {
    'schema': HUMAN_PLAN_SCHEMA,
    'dataset_version': 'fccdffc984dca0b30d9c044ee62bee32eb52b3b4a828fe454e6a17de0602fd26',
    's5b_protocol_identities': {
        'H1': 'b8137660098a04d63ff11500ce4d3c2c23f7fd2dee23bb7fb3020ca77a5996cc',
        'H2': '9ea49ccfba23361bdae8816e29bbf07817894edca79710f1816da8901e8edd7a',
    },
    'source_rubric_sha256': 'e805b86423b4a6e46e2b3a2f577dd4b8b66419b8b2270cd5eb31a785f6d579a2',
    'seed': 20261025, 'expected_cells': 16, 'observations_per_cell': 5,
    'extra_nonancestral': 16, 'target_observations': 96,
    'assessors': ['A1', 'A2'], 'unit': 'sentence_pair', 'modality': 'human_blind_pending',
    'selection': 'five_per_method_severity_cell_plus_sixteen_nonancestral_text_deduplicated',
    'presentation': 'opaque_content_ids_and_separate_hash_order_per_assessor',
    'disagreement_policy': {'H1': 'agreement_only_else_null', 'H2': 'mean_if_both_labeled_else_null',
                            'individual_scores': 'preserve_and_report_each_assessor'},
    'agreement': {'H1': 'nominal_cohen_kappa', 'H2': 'spearman_average_ranks',
                  'undefined': 'null_with_reason', 'scope': 'finite_dependent_set_no_population_CI'},
    'test_predictions_authorized': False,
}


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def validate_human_plan(plan):
    fields(plan, set(HUMAN_DEFAULTS) | {'rubric_sha256', 'frozen_inputs_identity'}, 'plano humano')
    for key, expected in HUMAN_DEFAULTS.items():
        # Canonical identities also distinguish booleans from integers.
        if identity(plan[key]) != identity(expected):
            raise ValueError('plano humano: campo não adotado: ' + key)
    for key in ('rubric_sha256', 'frozen_inputs_identity'):
        value = plan[key]
        if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('plano humano: SHA-256 inválido: ' + key)
    return identity(plan)


def select_human_pairs(data, plan):
    sources = {source['id']: source for source in data['sources']}
    pairs = [pair for pair in data['pairs'] if pair['split'] == 'test']
    cells = defaultdict(list)
    for pair in pairs:
        if sources[pair['source_id']]['split'] != 'test':
            raise ValueError('fonte fora do split test')
        cells[(pair['method'], str(pair['severity']))].append(pair)
    if len(cells) != plan['expected_cells']:
        raise ValueError('cobertura método/severidade diverge do plano; não ampliar silenciosamente')
    selected, seen, used_documents, used_suspects = [], set(), set(), set()

    def document_key(pair):
        return (pair['source_id'], tuple(row['semantic'] for row in pair['sentences']))

    def take(candidates, cross=False):
        ordered = sorted(candidates, key=lambda p: (document_key(p) in used_documents,
                         text_hash(str(plan['seed']) + ':' + p['id'])))
        for pair in ordered:
            source = sources[pair['source_id']]
            for suspect in sorted(pair['sentences'], key=lambda row: (
                text_hash(row['semantic']) in used_suspects,
                text_hash(str(plan['seed']) + ':' + pair['id'] + ':' + row['id']),
            )):
                ancestors = {a['sentence_id'] for a in suspect['ancestors'] if a['source_id'] == source['id']}
                for sentence in sorted(source['sentences'], key=lambda row: (
                    row['id'] not in ancestors, text_hash(str(plan['seed']) + ':' + row['id']),
                )):
                    if cross and sentence['id'] in ancestors:
                        continue
                    hashes = (text_hash(sentence['semantic']), text_hash(suspect['semantic']))
                    if hashes in seen:
                        continue
                    seen.add(hashes)
                    used_documents.add(document_key(pair))
                    used_suspects.add(hashes[1])
                    selected.append({
                        'observation_id': 'Q-' + identity(hashes)[:16],
                        'pair_id': pair['id'], 'source_id': source['id'],
                        'source_sentence_id': sentence['id'], 'suspect_sentence_id': suspect['id'],
                        'source_text_sha256': hashes[0], 'suspect_text_sha256': hashes[1],
                        'source_text': sentence['semantic'], 'suspect_text': suspect['semantic'],
                        'split': 'test', 'method': pair['method'], 'severity': pair['severity'],
                        'stratum': 'nonancestral_cross' if cross else 'method_severity',
                        'ancestral_pair': sentence['id'] in ancestors,
                    })
                    return
        raise ValueError('cobertura insuficiente sem pares textuais duplicados; preservar tentativa')

    for _ in range(plan['observations_per_cell']):
        for key in sorted(cells):
            take(cells[key])
    for _ in range(plan['extra_nonancestral']):
        take(pairs, cross=True)
    if len(selected) != plan['target_observations'] or len({r['observation_id'] for r in selected}) != len(selected):
        raise ValueError('quantidade ou IDs opacos divergem do plano')
    return selected


def blind_packet(selection, plan, assessor_id, rubric):
    if assessor_id not in plan['assessors']:
        raise ValueError('destino de participante desconhecido')
    rows = sorted(selection, key=lambda row: text_hash(str(plan['seed']) + ':' + assessor_id + ':' + row['observation_id']))
    packet = {'schema': 'hts-human-packet-1', 'assessor_id': assessor_id,
              'campaign_identity': identity({'plan': identity(plan), 'selection': identity(selection)}),
              'rubric': rubric,
              'items': [{'observation_id': row['observation_id'], 'text_a': row['source_text'], 'text_b': row['suspect_text']} for row in rows]}
    packet['packet_identity'] = identity(packet)
    return packet


def render_packet(packet):
    template = (CORE / 'assets/human-reference/form.html').read_text(encoding='utf-8')
    payload = json.dumps(packet, ensure_ascii=False, allow_nan=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    payload = payload.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    if template.count('@@PACKET_JSON@@') != 1:
        raise ValueError('marcador de formulário inválido')
    return template.replace('@@PACKET_JSON@@', payload)


def validate_preparation_inputs(plan, rubric, reference, h1_protocol, h2_protocol):
    plan_id = validate_human_plan(plan)
    for task, path in (('H1', h1_protocol), ('H2', h2_protocol)):
        protocol = read_json(path)
        if validate_s5b(protocol) != plan['s5b_protocol_identities'][task] or protocol['dataset_version'] != plan['dataset_version']:
            raise ValueError('protocolo/modelos congelados divergem: ' + task)
        if identity(read_json(reference)) != protocol['reference_protocol_identity']:
            raise ValueError('protocolo estrutural S5A diverge')
    if sha(CORE / 'assets/rubrics/s5b-rubric-01.md') != plan['source_rubric_sha256'] or sha(rubric) != plan['rubric_sha256']:
        raise ValueError('rubrica original ou humana alterada')
    return plan_id


def prepare_human_reference(plan, rubric, reference, h1_protocol, h2_protocol,
                            authorization_record, dataset, frozen_inputs, destination):
    plan_id = validate_preparation_inputs(plan, rubric, reference, h1_protocol, h2_protocol)
    authorization = read_json(authorization_record)
    fields(authorization, {'action', 'plan_identity', 'user_instruction_file', 'user_instruction_sha256',
                            'predictions_authorized'}, 'autorização')
    if authorization['action'] != 'prepare_blind_human_reference' or authorization['plan_identity'] != plan_id or authorization['predictions_authorized'] is not False:
        raise PermissionError('autorização cega deve vincular o plano e manter predições fechadas')
    if sha(authorization['user_instruction_file']) != authorization['user_instruction_sha256']:
        raise PermissionError('bytes da instrução real divergem da autorização')
    frozen = read_json(frozen_inputs)
    fields(frozen, {'schema', 'files'}, 'inventário de entradas congeladas')
    if frozen['schema'] != 'hts-s5c-frozen-inputs-1' or identity(frozen) != plan['frozen_inputs_identity'] or not frozen['files']:
        raise ValueError('inventário de modelos e recursos difere do plano')
    for name, expected in frozen['files'].items():
        path = (CORE.parent / name).resolve()
        if not path.is_relative_to(CORE.parent.resolve()) or sha(path) != expected:
            raise ValueError('entrada científica congelada alterada: ' + name)
    out = Path(destination)
    if out.exists():
        raise FileExistsError('destino já existe; usar nova tentativa e preservar anteriores')
    data = inspect_dataset(dataset, read_json(reference))
    if data['manifest']['version'] != plan['dataset_version']:
        raise ValueError('dataset final diverge do plano')
    selection = select_human_pairs(data, plan)
    rubric_text = Path(rubric).read_text(encoding='utf-8')
    out.mkdir(parents=True, exist_ok=False)
    for name, value in (('plan.json', plan), ('authorization.json', authorization),
                        ('frozen-inputs.json', frozen), ('selection-private.json', selection)):
        save_json_new(out / name, value)
    counts = Counter((row['method'], str(row['severity'])) for row in selection if row['stratum'] == 'method_severity')
    coverage = {'selected': len(selection), 'unique_text_pairs': len({(r['source_text_sha256'], r['suspect_text_sha256']) for r in selection}),
                'unique_source_texts': len({r['source_text_sha256'] for r in selection}),
                'unique_suspect_texts': len({r['suspect_text_sha256'] for r in selection}),
                'sources': len({r['source_id'] for r in selection}),
                'document_pairs': len({r['pair_id'] for r in selection}),
                'method_severity': [{'method': key[0], 'severity': key[1], 'count': count} for key, count in sorted(counts.items())],
                'extra_nonancestral': sum(r['stratum'] == 'nonancestral_cross' for r in selection),
                'independent_observations_claimed': False}
    save_json_new(out / 'coverage-private.json', coverage)
    for assessor in plan['assessors']:
        packet = blind_packet(selection, plan, assessor, rubric_text)
        save_json_new(out / 'packets' / (assessor + '.json'), packet)
        send = out / assessor
        send.mkdir()
        (send / 'avaliacao.html').write_text(render_packet(packet), encoding='utf-8')
        (send / 'rubrica.md').write_text(rubric_text, encoding='utf-8')
        (send / 'LEIA-ME.txt').write_text(
            f'Você recebeu o pacote do participante {assessor}.\n\n'
            '1. Extraia este ZIP em uma pasta e abra avaliacao.html no Chrome ou Edge de computador.\n'
            '2. Leia as instruções e avalie individualmente todos os pares. Não use IA nem consulte outra pessoa.\n'
            '3. Seu código basta: não informe nome, e-mail ou documento pessoal. Declare vínculo e exposição anterior com sinceridade.\n'
            '4. Use Salvar rascunho para baixar uma cópia JSON. Para retomar, use Retomar arquivo.\n'
            '5. No fim, preencha a declaração e clique Exportar respostas finais. Envie o JSON final ao pesquisador.\n\n'
            'O formulário funciona offline. Nenhuma resposta é enviada automaticamente.\n'
            'O salvamento local depende do navegador; guarde os rascunhos JSON para não perder trabalho.\n'
            'A rubrica também está em rubrica.md. Não compartilhe respostas com o outro participante.\n', encoding='utf-8')
        save_json_new(send / 'integridade.json', {p.name: sha(p) for p in sorted(send.iterdir())})
        with zipfile.ZipFile(out / (assessor + '.zip'), 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(send.iterdir()):
                info = zipfile.ZipInfo(path.name, date_time=(2026, 10, 27, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
    save_json_new(out / 'preparation-receipt.json', {
        'schema': 'hts-human-preparation-receipt-1', 'utc': datetime.now(timezone.utc).isoformat(),
        'plan_identity': plan_id, 'authorization_identity': identity(authorization),
        'selection_identity': identity(selection), 'selected': len(selection),
        'test_texts_exposed_for_annotation': True, 'labels_produced': 0,
        'human_participants_identified': False, 'reference_frozen': False, 'predictions': False,
        'files': {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob('*')) if p.is_file()},
    })
    return {'status': 'blind_human_inputs_prepared', 'selected': len(selection),
            'assessor_codes': plan['assessors'], 'human_answers': 0, 'predictions': False}


def validate_submission(submission, packet):
    fields(submission, {'schema', 'campaign_identity', 'packet_identity', 'assessor_id',
                        'complete', 'completed_at', 'declaration', 'records'}, 'respostas')
    if submission['schema'] != 'hts-human-response-1' or submission['complete'] is not True:
        raise ValueError('respostas finais completas exigidas; rascunho não é anotação final')
    for key in ('campaign_identity', 'packet_identity', 'assessor_id'):
        if submission[key] != packet[key]:
            raise ValueError('respostas pertencem a outro pacote: ' + key)
    if type(submission['completed_at']) is not str:
        raise ValueError('data real de conclusão exigida')
    try:
        completed = datetime.fromisoformat(submission['completed_at'].replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValueError('data de conclusão inválida') from exc
    if completed.tzinfo is None:
        raise ValueError('data de conclusão exige fuso horário')
    declaration = submission['declaration']
    flags = {'human', 'independent', 'no_ai', 'no_collaboration', 'participated_in_creation'}
    fields(declaration, flags | {'project_relationship', 'prior_exposure', 'exposure_details'}, 'declaração')
    for flag in flags:
        if type(declaration[flag]) is not bool:
            raise ValueError('declaração exige booleano: ' + flag)
    nonempty(declaration['project_relationship'], 'vínculo com o projeto')
    if declaration['prior_exposure'] not in ('none', 'yes') or type(declaration['exposure_details']) is not str:
        raise ValueError('exposição anterior deve ser declarada')
    if declaration['prior_exposure'] == 'yes':
        nonempty(declaration['exposure_details'], 'detalhes da exposição')
    records = submission['records']
    if type(records) is not list:
        raise ValueError('records: lista exigida')
    expected = {item['observation_id']: item for item in packet['items']}
    seen = set()
    for row in records:
        fields(row, {'observation_id', 'H1', 'H2'}, 'resposta')
        key = row['observation_id']
        if type(key) is not str or key not in expected or key in seen:
            raise ValueError('ID desconhecido ou duplicado nas respostas')
        seen.add(key)
        for task in ('H1', 'H2'):
            validate_judgment(row[task], task, expected[key])
    if seen != set(expected):
        raise ValueError('respostas não cobrem exatamente todos os pares selecionados')
    return {'human_independence_declared': all(declaration[key] for key in flags - {'participated_in_creation'})
            and not declaration['participated_in_creation'] and declaration['prior_exposure'] == 'none',
            'identity_authenticated': False,
            'counts': {task: dict(Counter(row[task]['status'] for row in records)) for task in ('H1', 'H2')}}


def audit_human_results(campaign, answer_paths, destination):
    campaign = Path(campaign)
    receipt = read_json(campaign / 'preparation-receipt.json')
    for relative, expected in receipt['files'].items():
        path = (campaign / relative).resolve()
        if not path.is_relative_to(campaign.resolve()) or sha(path) != expected:
            raise ValueError('pacote preparado foi alterado: ' + relative)
    plan = read_json(campaign / 'plan.json')
    if validate_human_plan(plan) != receipt['plan_identity']:
        raise ValueError('plano preparado foi alterado')
    paths = [Path(path) for path in answer_paths]
    if len(paths) != 2 or paths[0].resolve() == paths[1].resolve():
        raise ValueError('dois arquivos de participantes distintos exigidos')
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    submissions = []
    try:
        # Preserva bytes brutos antes de validar qualquer resposta.
        for index, path in enumerate(paths, 1):
            (out / f'raw-{index}.json').write_bytes(path.read_bytes())
        reports = {}
        for index in (1, 2):
            submission = read_json(out / f'raw-{index}.json')
            assessor = submission.get('assessor_id')
            if assessor not in plan['assessors'] or assessor in reports:
                raise ValueError('código de participante desconhecido ou repetido')
            packet = read_json(campaign / 'packets' / (assessor + '.json'))
            reports[assessor] = validate_submission(submission, packet)
            submissions.append(submission)
        agreement = agreement_and_consensus(*submissions)
        independent = all(report['human_independence_declared'] for report in reports.values())
        save_json_new(out / 'agreement.json', agreement)
        save_json_new(out / 'individual-responses.json', submissions)
        result: dict[str, Any] = {
            'schema': 'hts-human-import-receipt-1', 'utc': datetime.now(timezone.utc).isoformat(),
            'plan_identity': receipt['plan_identity'], 'selection_identity': receipt['selection_identity'],
            'assessors': reports, 'human_independence_declared': independent,
            'identity_authenticated': False, 'reference_frozen': False, 'predictions': False,
            'status': 'audited_pending_reference_freeze' if independent else 'audited_independence_not_declared',
            'files': {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()},
        }
        save_json_new(out / 'import-receipt.json', result)
        return result
    except Exception as exc:
        save_json_new(out / 'failure.json', {'type': type(exc).__name__, 'reason': str(exc),
                      'reference_frozen': False, 'predictions': False,
                      'raw_files': {p.name: sha(p) for p in out.glob('raw-*.json')}})
        raise
