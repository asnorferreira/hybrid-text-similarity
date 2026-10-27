"""Reload frozen models on validation; recalculate P10 saved predictions only.

Run with the core Docker image after private resources have been restored.
No optimizer, fitting, calibration or scientific test inference is invoked.
"""
import argparse
import hashlib
import json
from pathlib import Path

import torch

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.experiment_io import annotation_examples, inspect_dataset
from hts_core.adapters.semantic import SemanticEncoder
from hts_core.adapters.trained_models import TrainedModels, load_config
from hts_core.adapters.training_baselines import predict_baseline
from hts_core.adapters.training_classifiers import predict_export
from hts_core.application.calibration import predict_platt
from hts_core.application.final_evaluation import reports_from_predictions


def check(root, output):
    core = root / 'core'
    protocol = read_json(core / 'configs/experiment_s5a.json')
    dataset = inspect_dataset(core / 'artifacts/artifacts/s4-fechamento-01/frozen-curated-01', protocol)
    annotation_dir = core / 'artifacts/artifacts/s5b-01'
    examples, _ = annotation_examples(read_json(annotation_dir / 'annotations-H1.json'), dataset, protocol, 'validation')
    run = core / 'artifacts/plan16-r3-01/H1-restart-01'
    expected = read_json(run / 'result.json')
    bindings = read_json(run / 'readiness.json')['bindings']
    records = [read_json(p) for p in sorted((run / 'features').glob('validation-*.json'))]
    assert len(records) == len(examples) == 17
    features = {key: [row['features'][key] for row in records] for key in expected['classifiers']}
    systems = {}
    for name in (*expected['classifiers'], *expected['baselines']):
        path = run / expected['artifacts'][name]['path']
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert sha == expected['artifacts'][name]['sha256']
        model = read_json(path)
        if name in expected['classifiers']:
            actual = predict_export(model, features[name], expected_bindings=bindings)
            saved = expected['classifiers'][name]['predictions']
        else:
            actual = predict_baseline(model, examples, features, bindings)
            saved = expected['baselines'][name]['validation_predictions']
        assert actual == saved
        systems[name] = {'n': len(actual), 'equal': True, 'sha256': sha}
    platt = read_json(run / 'calibration/platt.json')
    observations = read_json(run / 'calibration/observations.json')
    scores = [row['score'] for row in observations]
    assert predict_platt(platt, scores, platt['bindings']) == predict_platt(
        expected['calibration']['model'], scores, platt['bindings'])

    torch.set_num_threads(2)
    encoder = SemanticEncoder()
    trained = TrainedModels(encoder, load_config())
    h2, _ = annotation_examples(read_json(annotation_dir / 'annotations-H2.json'), dataset, protocol, 'validation')
    h2_run = core / 'artifacts/plan16-r4-01/H2-scientific-01'
    result = read_json(h2_run / 'result.json')
    best = min(result['history'], key=lambda row: (row['validation']['mse'], row['epoch']))
    assert len(h2) == len(best['predictions']) == 13
    values = []
    with torch.no_grad():
        for row in h2:
            values.append(float(trained.siamese(row['input'].source_text, row['input'].suspect_text)))
    error = max(abs(a - b) for a, b in zip(values, best['predictions'], strict=True))
    assert error <= 1e-6
    p9 = root / 'TCC/evidencias/codex-p09-02'
    p10 = root / 'TCC/evidencias/codex-p10-01/avaliacao-01'
    reference = read_json(p9 / 'referencia-final-01.json')
    predictions = read_json(p10 / 'predictions.json')
    metrics = read_json(p10 / 'metrics.json')
    assert len(reference['records']) == len(predictions) == 96
    assert json.loads(json.dumps(reports_from_predictions(reference['records'], predictions))) == metrics
    report = {'status': 'passed', 'H1_validation': systems,
              'Platt_validation': {'n': len(scores), 'equal': True},
              'H2_validation': {'n': len(values), 'maximum_error': error, 'tolerance': 1e-6},
              'P10_saved_recalculation': {'n': 96, 'exact': True},
              'scientific_test_inference_repeated': False, 'training_repeated': False,
              'shared_encoder': trained.siamese.encoder.model is encoder.model}
    with output.open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    check(args.root, args.out)
