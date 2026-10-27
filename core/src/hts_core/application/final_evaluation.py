"""Frozen S5C reference and a single, explicitly authorized evaluation."""
from datetime import datetime, timezone
from pathlib import Path
import math

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.experiment_io import inspect_dataset, save_json_new
from hts_core.application.human_reference import sha, validate_human_plan, validate_submission
from hts_core.domain.experiments import ModelInput, classification_report, regression_report, validate_outputs
from hts_core.domain.human_reference import CLASSES, agreement_and_consensus


SYSTEMS = ('lexical', 'semantic', 'fixed_fusion', 'learned_fusion', 'baseline_q5v2', 'baseline_majority')
H2_SYSTEMS = ('sbert', 'siamese')


def checked_path(root, relative):
    root = Path(root).resolve()
    if type(relative) is not str or Path(relative).is_absolute():
        raise ValueError('repository-relative path required')
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('path outside repository')
    return path


def verify_files(root, files):
    if type(files) is not dict or not files:
        raise ValueError('nonempty frozen inventory required')
    for relative, expected in files.items():
        if sha(checked_path(root, relative)) != expected:
            raise ValueError('frozen file changed: ' + relative)


def eligibility(rows, minimum=8):
    counts = {}
    for task in ('H1', 'H2'):
        targets = [row[task]['target'] for row in rows if row[task]['target'] is not None]
        distinct = len(set(targets))
        counts[task] = {'n': len(targets), 'distinct_targets': distinct,
                        'eligible': len(targets) >= minimum and (task == 'H1' or distinct >= 2)}
    counts['H1']['class_counts'] = {label: sum(row['H1']['target'] == label for row in rows) for label in CLASSES}
    counts['H1']['absent_classes'] = [c for c, n in counts['H1']['class_counts'].items() if n == 0]
    return counts


def validate_model_plan(root, plan, inventory, human_plan):
    """All model choices must already belong to the pre-annotation inventory."""
    checkpoint = checked_path(root, plan['h2_checkpoint'])
    required = [plan['idf'], plan['h2_protocol'], plan['platt']]
    required += [(Path(plan['h1']) / (system + '.json')).as_posix() for system in SYSTEMS]
    required += [(Path(plan['h2_checkpoint']) / name).as_posix()
                 for name in ('manifest.json', 'weights.safetensors', 'local-state.pt')]
    required.append((Path(plan['h2_checkpoint']).parent / 'result.json').as_posix())
    for relative in required:
        if relative not in inventory or sha(checked_path(root, relative)) != inventory[relative]:
            raise ValueError('model/resource absent from preselection freeze: ' + relative)
    from hts_core.adapters.training_classifiers_v2 import validate_export
    for system in SYSTEMS:
        export = read_json(checked_path(root, plan['h1']) / (system + '.json'))
        if (export['bindings']['dataset'] != human_plan['dataset_version'] or
                export['bindings']['protocol'] != human_plan['s5b_protocol_identities']['H1'] or export['system'] != system):
            raise ValueError('H1 model bindings differ')
        if not system.startswith('baseline_'):
            validate_export(export)
    manifest = read_json(checkpoint / 'manifest.json')
    if (manifest['bindings']['protocol'] != human_plan['s5b_protocol_identities']['H2'] or
            manifest['bindings']['dataset'] != human_plan['dataset_version'] or
            Path(read_json(checkpoint.parent / 'result.json')['best_checkpoint']).name != checkpoint.name):
        raise ValueError('H2 differs from preselected checkpoint')
    platt = read_json(checked_path(root, plan['platt']))
    if (platt['fit_split'] != 'validation' or platt['target'] != 'sentence_pair_derivation' or
            platt['bindings']['dataset'] != human_plan['dataset_version'] or
            platt['identity'] != identity({k: v for k, v in platt.items() if k != 'identity'})):
        raise ValueError('P1 calibration bindings differ')


def freeze_reference(root, campaign, imported, plan_path, destination):
    """No inference: verify the preselection inventory, raw answers and text bindings."""
    root = Path(root).resolve()
    campaign, imported = Path(campaign), Path(imported)
    preparation = read_json(campaign / 'preparation-receipt.json')
    for name, expected in preparation['files'].items():
        if sha(checked_path(campaign, name)) != expected:
            raise ValueError('prepared campaign changed: ' + name)
    human_plan = read_json(campaign / 'plan.json')
    if validate_human_plan(human_plan) != preparation['plan_identity']:
        raise ValueError('human plan differs')
    original = read_json(campaign / 'frozen-inputs.json')
    if identity(original) != human_plan['frozen_inputs_identity']:
        raise ValueError('preselection inventory differs')
    # Only CLI routing may change while adding this runner. Scientific resources
    # and scoring implementations selected before annotation must remain exact.
    routing = 'core/src/hts_core/cli/experiment.py'
    changed = {}
    for relative, expected in original['files'].items():
        actual = sha(checked_path(root, relative))
        if actual != expected:
            if relative != routing:
                raise ValueError('preselection scientific input changed: ' + relative)
            changed[relative] = {'before': expected, 'after': actual, 'reason': 'add frozen evaluation CLI routing'}
    receipt = read_json(imported / 'import-receipt.json')
    if (receipt['status'] != 'audited_pending_reference_freeze' or
            receipt['human_independence_declared'] is not True or
            receipt['plan_identity'] != preparation['plan_identity'] or
            receipt['selection_identity'] != preparation['selection_identity']):
        raise PermissionError('two audited, independently declared final submissions required')
    for name, expected in receipt['files'].items():
        if sha(checked_path(imported, name)) != expected:
            raise ValueError('imported response changed: ' + name)
    answers = [read_json(imported / f'raw-{index}.json') for index in (1, 2)]
    for response in answers:
        if not validate_submission(response, read_json(campaign / 'packets' / (response['assessor_id'] + '.json')))['human_independence_declared']:
            raise PermissionError('independence not declared')
    agreement = agreement_and_consensus(*answers)
    if agreement != read_json(imported / 'agreement.json'):
        raise ValueError('agreement differs from preserved raw responses')
    selection = read_json(campaign / 'selection-private.json')
    if identity(selection) != receipt['selection_identity']:
        raise ValueError('preselected IDs differ')
    plan = read_json(plan_path)
    if (plan['schema'] != 'hts-s5c-evaluation-plan-1' or plan['minimum_valid'] != 8 or
            plan['scope'] != 'finite_dependent_human_subset_no_population_inference'):
        raise ValueError('evaluation plan differs from adopted scope')
    validate_model_plan(root, plan, original['files'], human_plan)
    dataset = inspect_dataset(checked_path(root, plan['dataset']), read_json(checked_path(root, plan['reference_protocol'])))
    if dataset['manifest']['version'] != human_plan['dataset_version']:
        raise ValueError('dataset identity differs')
    sources = {s['id']: s for s in dataset['sources']}
    pairs = {p['id']: p for p in dataset['pairs']}
    consensus = {row['observation_id']: row for row in agreement['consensus']}
    records = []
    individual = {answer['assessor_id']: {row['observation_id']: row for row in answer['records']} for answer in answers}
    for row in selection:
        pair, source = pairs[row['pair_id']], sources[row['source_id']]
        a = next(s for s in source['sentences'] if s['id'] == row['source_sentence_id'])
        b = next(s for s in pair['sentences'] if s['id'] == row['suspect_sentence_id'])
        if (pair['split'] != 'test' or source['split'] != 'test' or
                a['semantic'] != row['source_text'] or b['semantic'] != row['suspect_text']):
            raise ValueError('selected text/split differs from frozen dataset')
        derivation = int(any(ancestor['source_id'] == row['source_id'] and
                             ancestor['sentence_id'] == row['source_sentence_id'] for ancestor in b['ancestors']))
        records.append({**row, 'H1': consensus[row['observation_id']]['H1'],
                         'H2': consensus[row['observation_id']]['H2'], 'derivation': derivation,
                         'individual': {assessor: {task: judgments[row['observation_id']][task] for task in ('H1', 'H2')}
                                        for assessor, judgments in individual.items()},
                         'format': 'canonical_text_not_additional_format_observations'})
    gates = eligibility(records, plan['minimum_valid'])
    if not all(gate['eligible'] for gate in gates.values()):
        raise PermissionError('insufficient frozen reference; preserve, do not expand after scores')
    files = {relative: sha(checked_path(root, relative)) for relative in original['files']}
    for folder in (campaign, imported):
        for path in folder.rglob('*'):
            if path.is_file() and path.name not in ('rascunho-A1.json', 'rascunho-A2.json'):
                files[path.resolve().relative_to(root).as_posix()] = sha(path)
    for path in (root / 'core/src').rglob('*.py'):
        files[path.relative_to(root).as_posix()] = sha(path)
    files[Path(plan_path).resolve().relative_to(root).as_posix()] = sha(Path(plan_path))
    body = {'schema': 'hts-final-reference-1', 'utc': datetime.now(timezone.utc).isoformat(),
            'reference_frozen': True, 'predictions': False,
            'campaign': campaign.resolve().relative_to(root).as_posix(),
            'human_plan_identity': preparation['plan_identity'],
            'plan_identity': identity(plan), 'evaluation_plan': plan,
            'dataset_version': human_plan['dataset_version'], 'files': files,
            'routing_changes_since_selection': changed,
            'human_independence': 'declared_by_two_codes_identity_not_authenticated',
            'scope': plan['scope'], 'records': records, 'eligibility': gates,
            'agreement': {k: v for k, v in agreement.items() if k != 'consensus'},
            'population_inference_claimed': False}
    body['identity'] = identity(body)
    save_json_new(destination, body)
    return body


def check_reference(reference, root):
    if (reference.get('schema') != 'hts-final-reference-1' or reference.get('reference_frozen') is not True or
            reference.get('identity') != identity({k: v for k, v in reference.items() if k != 'identity'})):
        raise PermissionError('verified frozen reference required before prediction')
    if reference['plan_identity'] != identity(reference['evaluation_plan']):
        raise ValueError('evaluation plan identity differs')
    rows = reference['records']
    if not rows or len({r['observation_id'] for r in rows}) != len(rows):
        raise ValueError('unique selected IDs required')
    if eligibility(rows) != reference['eligibility'] or not all(g['eligible'] for g in reference['eligibility'].values()):
        raise PermissionError('reference eligibility differs')
    verify_files(root, reference['files'])


def reports_from_predictions(records, predictions):
    if len(predictions) != len(records) or [p['observation_id'] for p in predictions] != [r['observation_id'] for r in records]:
        raise ValueError('prediction coverage/order differs')
    result = {}
    for task, systems in (('H1', SYSTEMS), ('H2', H2_SYSTEMS)):
        selected = [(r, p) for r, p in zip(records, predictions, strict=True) if r[task]['target'] is not None]
        truth = [r[task]['target'] for r, _ in selected]
        result[task] = {}
        for system in systems:
            values = validate_outputs([p[task][system] for _, p in selected], len(selected), task, CLASSES)
            result[task][system] = classification_report(truth, values, CLASSES) if task == 'H1' else regression_report(truth, values)
    from hts_core.domain.calibration import calibration_metrics
    result['P1'] = {'scope': 'selected_pairs_synthetic_derivation_not_semantic_truth',
                    'raw': calibration_metrics([r['derivation'] for r in records], [p['P1']['raw'] for p in predictions]),
                    'calibrated': calibration_metrics([r['derivation'] for r in records], [p['P1']['probability'] for p in predictions])}
    result['P1']['q5v2_decision'] = classification_report([r['derivation'] for r in records],
                                                        [p['P1']['q5v2_derived'] for p in predictions], (0, 1))
    result['individual_assessors'] = {}
    for assessor in sorted(records[0].get('individual', {})):
        result['individual_assessors'][assessor] = {}
        for task, systems in (('H1', SYSTEMS), ('H2', H2_SYSTEMS)):
            valid = [(r, p) for r, p in zip(records, predictions, strict=True)
                     if r['individual'][assessor][task]['status'] == 'labeled']
            truth = [r['individual'][assessor][task]['target'] for r, _ in valid]
            result['individual_assessors'][assessor][task] = {
                system: ((classification_report(truth, [p[task][system] for _, p in valid], CLASSES) if task == 'H1' else
                          regression_report(truth, [p[task][system] for _, p in valid])) if valid else
                         {'n': 0, 'value': None, 'reason': 'no eligible targets'}) for system in systems}
    result['strata'] = {}
    for field in ('method', 'severity', 'format'):
        result['strata'][field] = {}
        for value in sorted({str(r[field]) for r in records}):
            group = [(r, p) for r, p in zip(records, predictions, strict=True) if str(r[field]) == value]
            item = {'selected': len(group), 'H1': {}, 'H2': {}}
            for task, systems in (('H1', SYSTEMS), ('H2', H2_SYSTEMS)):
                valid = [(r, p) for r, p in group if r[task]['target'] is not None]
                for system in systems:
                    truth, values = [r[task]['target'] for r, _ in valid], [p[task][system] for _, p in valid]
                    item[task][system] = (classification_report(truth, values, CLASSES) if task == 'H1' else
                                          regression_report(truth, values)) if valid else {'n': 0, 'value': None, 'reason': 'no eligible targets'}
            result['strata'][field][value] = item
    result['population_inference_claimed'] = False
    return result


def claim_path(root, reference):
    name = identity([reference['dataset_version'], reference['human_plan_identity']]) + '.json'
    return checked_path(root, 'core/artifacts/s5c-claims/' + name)


def evaluate(reference_path, authorization_path, authorization_sha256, root, destination, *, predictor_factory=None):
    reference = read_json(reference_path)
    check_reference(reference, root)
    auth = read_json(authorization_path)
    if (sha(Path(authorization_path)) != authorization_sha256 or
            auth.get('action') != 'evaluate_final_once' or auth.get('predictions_authorized') is not True or
            auth.get('reference_identity') != reference['identity'] or auth.get('split') != 'test' or
            sha(checked_path(root, auth['user_instruction_file'])) != auth['user_instruction_sha256']):
        raise PermissionError('authorization hash/instruction/reference required')
    out = Path(destination)
    if out.exists():
        raise FileExistsError('preserve previous evaluation destination')
    # Fixed campaign claim is shared across destinations and reference revisions.
    claim = claim_path(root, reference)
    save_json_new(claim, {'reference_identity': reference['identity'], 'authorization_sha256': authorization_sha256,
                         'utc': datetime.now(timezone.utc).isoformat(), 'destination': str(out), 'automatic_retry': False})
    out.mkdir(parents=True, exist_ok=False)
    try:
        predictor = (predictor_factory or FrozenPredictor)(root, reference['evaluation_plan'])
        predictions = []
        for row in reference['records']:
            prediction = predictor(ModelInput(row['source_text'], row['suspect_text']))
            value = {'observation_id': row['observation_id'], **prediction}
            for task, systems in (('H1', SYSTEMS), ('H2', H2_SYSTEMS)):
                if set(value[task]) != set(systems):
                    raise ValueError('incomplete comparable systems')
                for v in value[task].values():
                    validate_outputs([v], 1, task, CLASSES)
            for key in ('raw', 'probability'):
                v = value['P1'][key]
                if type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1:
                    raise ValueError('invalid P1 output')
            if type(value['P1']['q5v2_derived']) is not int or value['P1']['q5v2_derived'] not in (0, 1):
                raise ValueError('invalid Q5-V2 derivation decision')
            save_json_new(out / 'predictions' / (row['observation_id'] + '.json'), value)
            predictions.append(value)
        reports = reports_from_predictions(reference['records'], predictions)
        save_json_new(out / 'predictions.json', predictions)
        save_json_new(out / 'metrics.json', reports)
        result = {'status': 'complete', 'reference_identity': reference['identity'], 'selected': len(predictions),
                  'eligible': reference['eligibility'], 'scope': reference['scope'],
                  'predictions_identity': identity(predictions), 'metrics_identity': identity(reports),
                  'utc': datetime.now(timezone.utc).isoformat(), 'single_attempt_claim': str(claim)}
        save_json_new(out / 'receipt.json', result)
        return result
    except Exception as exc:
        save_json_new(out / 'failure.json', {'type': type(exc).__name__, 'reason': str(exc),
                      'claim_preserved': True, 'automatic_retry': False})
        raise


class FrozenPredictor:
    """One shared pinned encoder; no fitting or access to labels/ancestry."""
    def __init__(self, root, plan):
        import torch
        from hts_core.adapters.semantic import SemanticEncoder
        from hts_core.adapters.trainable_siamese import Siamese, WindowEncoder
        from hts_core.adapters.training_artifacts import load_inference_weights
        from hts_core.domain.lexical import ReferenceIdf
        self.root, self.plan = Path(root), plan
        self.encoder = SemanticEncoder()
        config = read_json(checked_path(root, plan['h2_protocol']))
        spec = config['siamese']
        self.siamese = Siamese(WindowEncoder(self.encoder.model, self.encoder.tokenizer, self.encoder.limit),
                              spec['embedding_dimension'], spec['dense_dimensions'][1], spec['dropout'],
                              spec['leaky_relu_alpha'], spec['layer_norm_epsilon'], spec['encoder_trainable'])
        checkpoint = checked_path(root, plan['h2_checkpoint'])
        self.load_receipt = load_inference_weights(checkpoint, self.siamese, read_json(checkpoint / 'manifest.json')['bindings'])
        self.siamese.eval()
        for parameter in self.siamese.parameters():
            parameter.requires_grad_(False)
        torch.set_num_threads(2)
        table = read_json(checked_path(root, plan['idf']))
        self.idf = ReferenceIdf(table['n_docs'], table['df'], table['version'])
        from hts_core.adapters.calibration_resources import load_p1_resources
        self.application_idf, self.policy, _ = load_p1_resources(self.encoder)
        self.classifiers = {system: read_json(checked_path(root, plan['h1']) / (system + '.json')) for system in SYSTEMS}
        self.platt = read_json(checked_path(root, plan['platt']))

    def __call__(self, inputs):
        if type(inputs) is not ModelInput:
            raise ValueError('only two texts accepted by prediction boundary')
        import numpy as np
        import torch
        from hts_core.adapters.nlp import STOPWORDS, analyze
        from hts_core.adapters.training_baselines import predict_baseline
        from hts_core.adapters.training_classifiers_v2 import predict_export
        from hts_core.application.calibration import predict_platt
        from hts_core.application.controlled_training import _h1_features
        from hts_core.domain.lexical import cosine
        from hts_core.domain.preprocess import lexical_tokens
        a, b = inputs.source_text, inputs.suspect_text
        tokens = [lexical_tokens(text, analyze, STOPWORDS) for text in (a, b)]
        lexical = cosine(*(self.idf.vector(t) for t in tokens))
        vectors, diagnostics = self.encoder.encode([a, b])
        semantic = float(np.clip(vectors[0] @ vectors[1], -1, 1))
        features = {key: [value] for key, value in _h1_features(lexical, semantic, True).items()}
        h1 = {}
        for system, model in self.classifiers.items():
            h1[system] = (predict_baseline(model, [{'input': inputs}], features, model['bindings'])[0] if system.startswith('baseline_') else
                           predict_export(model, features[system], expected_bindings=model['bindings'])[0])
        with torch.no_grad():
            siamese = float(self.siamese(a, b))
        app_lexical = cosine(*(self.application_idf.vector(t) for t in tokens))
        raw = .4 * max(0., min(1., app_lexical)) + .6 * max(0., semantic)
        from hts_core.domain.hybrid import classify_pair
        from hts_core.domain.strings import levenshtein
        thresholds = {key: self.policy[key] for key in ('edited_threshold', 'low_threshold', 'paraphrase_threshold', 'lexical_high')}
        q5 = classify_pair(a, b, app_lexical, max(0, semantic), levenshtein(a, b), **thresholds)['label']
        return {'H1': h1, 'H2': {'sbert': (semantic + 1) / 2, 'siamese': siamese},
                'P1': {'raw': raw, 'probability': predict_platt(self.platt, [raw], self.platt['bindings'])[0],
                       'q5v2_derived': int(q5 != 'sem_correspondencia_detectada')},
                'features': features, 'token_windows': diagnostics}
