import json
from pathlib import Path

import pytest

from hts_core.adapters import trained_models
from hts_core.adapters.semantic import ResourceUnavailable
from hts_core.adapters.schemas import ComparisonResult


def test_trained_models_disabled_by_default(monkeypatch):
    monkeypatch.delenv('HTS_TRAINED_MODELS_CONFIG', raising=False)
    assert trained_models.load_config()['enabled'] is False


@pytest.mark.parametrize('fault', ['missing', 'boolean', 'extra', 'absolute', 'escape', 'schema', 'no_inventory'])
def test_trained_configuration_fails_explicitly(tmp_path, monkeypatch, fault):
    value = json.loads((trained_models.CORE/'configs/trained_models.json').read_text())
    if fault == 'boolean':
        value['enabled'] = 1
    elif fault == 'extra':
        value['r'] = 1
    elif fault == 'absolute':
        value['h1'] = '/etc/passwd'
    elif fault == 'escape':
        value['h1'] = '../escape'
    elif fault == 'schema':
        value['schema'] = 'future'
    elif fault == 'no_inventory':
        value['enabled'], value['files'] = True, {}
    path = tmp_path/'config.json'
    if fault != 'missing':
        path.write_text(json.dumps(value))
    monkeypatch.setenv('HTS_TRAINED_MODELS_CONFIG', str(path))
    with pytest.raises(ResourceUnavailable):
        trained_models.load_config()


def test_disabled_contract_omits_new_field():
    root = Path(__file__).resolve().parents[2]
    response = json.loads((root/'contracts/responses.json').read_text())['valid'][0]
    assert 'trained_models' not in response
    assert ComparisonResult.model_validate(response).model_dump(exclude_unset=True) == response


def test_enabled_missing_artifact_is_not_silently_disabled(tmp_path):
    config = trained_models.load_config()
    config['enabled'] = True
    config['h1'] = 'artifacts/missing-fixture.json'
    with pytest.raises(ResourceUnavailable):
        trained_models.TrainedModels(None, config)


def test_learned_features_preserve_training_cosine_roundoff_policy(monkeypatch):
    import torch
    from threading import Lock
    from types import SimpleNamespace
    from hts_core.adapters import training_classifiers_v2
    from hts_core.adapters.trainable_siamese import Siamese
    from hts_core.application import calibration
    from hts_core.domain import lexical
    from hts_core.domain.lexical import ReferenceIdf
    features = []
    monkeypatch.setattr(lexical, 'cosine', lambda a, b: 1. + 2.**-52)
    def predict(model, values, **kwargs):
        features.extend(values)
        return ['copia_exata']
    monkeypatch.setattr(training_classifiers_v2, 'predict_export', predict)
    monkeypatch.setattr(calibration, 'predict_platt', lambda *args: [.5])
    trained = trained_models.TrainedModels.__new__(trained_models.TrainedModels)
    trained.encoder = SimpleNamespace(lock=Lock())
    trained.idf = ReferenceIdf(1, {'texto': 1}, 'roundoff-fixture')
    trained.h1 = {'bindings': {}}
    trained.platt = {'bindings': {}}
    class FixtureEncoder(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.diagnostics = []
        def forward(self, text):
            self.diagnostics.append({'tokens': 1})
            return torch.tensor([1., 0.])
    trained.siamese = Siamese(FixtureEncoder(), dimension=2, hidden=2, train_encoder=False)
    trained.identities, trained.config_sha256 = [], 'a'*64
    sentence = {'semantic': 'Texto.', 'lexical': ['texto']}
    result = {'source': [sentence], 'suspect': [sentence], 'index': {'value': 100.},
              'matches': [{'source': 0, 'suspect': 0, 'semantic_raw': 1., 'fused': 1.}], 'metadata': {}}
    trained.enrich(result)
    assert features == [[1., 1.]]
    assert result['index'] == {'value': 100.}
    assert result['trained_models']['pairs'][0]['derivation_probability'] == .5
    assert trained.siamese.encoder.diagnostics == []
    monkeypatch.setattr(lexical, 'cosine', lambda a, b: 1.001)
    with pytest.raises(ValueError):
        trained.enrich(result)


def test_h2_serving_uses_native_pooling_instead_of_app_window_normalization(monkeypatch):
    import torch
    from threading import Lock
    from types import SimpleNamespace
    from hts_core.adapters import training_classifiers_v2
    from hts_core.adapters.trainable_siamese import Siamese
    from hts_core.application import calibration
    from hts_core.domain.lexical import ReferenceIdf

    # Two equal-sized windows with vectors [10,0] and [0,1] yield native
    # normalize([10,1]); normalizing each window first yields normalize([1,1]).
    class NativePool(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.diagnostics = []
        def forward(self, text):
            self.diagnostics.append({'tokens': 2})
            value = torch.tensor([10., 1.] if text == 'wide' else [1., 1.])
            return torch.nn.functional.normalize(value, dim=0)
    trained = trained_models.TrainedModels.__new__(trained_models.TrainedModels)
    trained.encoder = SimpleNamespace(lock=Lock(), encode=lambda texts: ([[2**-.5, 2**-.5]]*2, []))
    trained.siamese = Siamese(NativePool(), dimension=2, hidden=2, train_encoder=False)
    linear = torch.nn.Linear(4, 1, bias=False)
    trained.siamese.head = torch.nn.Sequential(linear, torch.nn.Sigmoid())
    with torch.no_grad():
        linear.weight.copy_(torch.tensor([[1., 0., 0., 0.]]))
        expected = float(trained.siamese('wide', 'other'))
    assert expected > .57  # The app's normalized-window shortcut would give .5.
    trained.idf = ReferenceIdf(1, {'texto': 1}, 'pooling-fixture')
    trained.h1, trained.platt = {'bindings': {}}, {'bindings': {}}
    trained.identities, trained.config_sha256 = [], 'a'*64
    monkeypatch.setattr(training_classifiers_v2, 'predict_export', lambda *args, **kwargs: ['copia_exata'])
    monkeypatch.setattr(calibration, 'predict_platt', lambda *args, **kwargs: [.5])
    result = {'source': [{'semantic': 'wide', 'lexical': ['texto']}],
              'suspect': [{'semantic': 'other', 'lexical': ['texto']}],
              'matches': [{'source': 0, 'suspect': 0, 'semantic_raw': 1., 'fused': 1.}], 'metadata': {}}
    trained.enrich(result)
    assert result['trained_models']['pairs'][0]['h2_score'] == expected
    assert trained.siamese.encoder.diagnostics == []
