import copy
import json
from pathlib import Path

import pytest

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.training_classifiers import predict_export, fit_classifiers, save_fitted_classifiers

CONFIG = read_json(Path(__file__).resolve().parents[1]/'configs/experiment_s5b.json')


def exported():
    value = {'schema':'hts-scalar-logistic-1','system':'lexical','classes':CONFIG['h1']['classes'],
             'coefficients':[[0.],[1.],[2.],[3.]],'intercepts':[0.,0.,0.,0.],
             'configuration':CONFIG['h1']['classifier'],'feature':['lexical_cosine'],
             'preprocessing':'one scalar unchanged; no standardization; no metadata features',
             'sklearn_version':'1.9.1','bindings':{'case':'artificial'}}
    value['identity'] = identity(value)
    return copy.deepcopy(value)


def test_literal_logits_and_json_roundtrip():
    value = json.loads(json.dumps(exported()))
    assert predict_export(value,[0.,1.]) == ['copia_exata','sem_correspondencia_detectada']


@pytest.mark.parametrize('case', ['classes','unknown','system','feature','configuration_bool','preprocessing',
                                'coefficient_bool','coefficient_string','intercept_bool','bindings'])
def test_rehashed_export_incompatible_contract_rejected(case):
    value = exported()
    if case == 'classes': value['classes'] = ['a','b','c','d']
    elif case == 'unknown': value['extra'] = 'ignored'
    elif case == 'system': value['system'] = 'construction_class'
    elif case == 'feature': value['feature'] = ['source_id']
    elif case == 'configuration_bool': value['configuration']['C'] = True
    elif case == 'preprocessing': value['preprocessing'] = 'hidden normalization'
    elif case == 'coefficient_bool': value['coefficients'][0][0] = True
    elif case == 'coefficient_string': value['coefficients'][0][0] = '1'
    elif case == 'intercept_bool': value['intercepts'][0] = True
    else: value['bindings'] = None
    value['identity'] = identity({k:v for k,v in value.items() if k != 'identity'})
    with pytest.raises(ValueError):
        predict_export(value,[.5])


@pytest.mark.parametrize('features', [[True],['.5'],[float('nan')],[float('inf')],[[.5]],[-.1],[1.1]])
def test_feature_types_and_lexical_range(features):
    with pytest.raises(ValueError):
        predict_export(exported(),features)


def test_external_expected_bindings_required_to_match():
    with pytest.raises(ValueError,match='bindings'):
        predict_export(exported(),[.5],expected_bindings={'case':'other'})


def test_fitted_artifacts_include_training_and_validation_reports():
    labels = CONFIG['h1']['classes']
    train = {s:[v for v in (.1,.3,.6,.9) for _ in range(2)] for s in ('lexical','semantic','fixed_fusion')}
    validation = {s:[.1,.3,.6,.9] for s in train}
    result = fit_classifiers(train,validation,[v for v in labels for _ in range(2)],labels,
                             CONFIG['h1'],{'case':'artificial'})
    for value in result.values():
        assert value['training']['n'] == 8
        assert sum(r['support'] for r in value['training']['per_class'].values()) == 8
        assert value['validation']['n'] == 4


def test_classifier_files_are_portable_and_bound(tmp_path):
    import shutil
    labels = CONFIG['h1']['classes']
    features = {s:[.1,.3,.6,.9] for s in ('lexical','semantic','fixed_fusion')}
    results = fit_classifiers(features,features,labels,labels,CONFIG['h1'],{'case':'artificial'})
    paths = save_fitted_classifiers(results,tmp_path/'producer',{'case':'artificial'})
    shutil.copytree(tmp_path/'producer',tmp_path/'relocated')
    for system,receipt in paths.items():
        assert receipt['loaded'] is True
        model = read_json(tmp_path/'relocated'/receipt['path'])
        assert predict_export(model,features[system],expected_bindings={'case':'artificial'}) == results[system]['predictions']


def test_relocated_siamese_weights_without_optimizer_or_rng(tmp_path,monkeypatch):
    import shutil
    import torch
    from hts_core.adapters.training_runtime import save_training_checkpoint
    from hts_core.adapters.training_artifacts import load_inference_weights
    source = torch.nn.Linear(1,1)
    with torch.no_grad():
        source.weight.fill_(2.)
        source.bias.fill_(1.)
    optimizer = torch.optim.Adam(source.parameters())
    save_training_checkpoint(tmp_path/'producer',source,optimizer,{'artificial':True},{'case':'artificial'})
    shutil.copytree(tmp_path/'producer',tmp_path/'relocated')
    def forbidden(*args,**kwargs):
        raise AssertionError('inference must not deserialize optimizer/RNG')
    monkeypatch.setattr(torch,'load',forbidden)
    target = torch.nn.Linear(1,1)
    receipt = load_inference_weights(tmp_path/'relocated',target,{'case':'artificial'})
    assert receipt['optimizer_and_rng_loaded'] is False
    assert target(torch.tensor([1.])).item() == 3.
    assert target.training is False
    with pytest.raises(ValueError,match='bindings'):
        load_inference_weights(tmp_path/'relocated',target,{'case':'other'})
    with (tmp_path/'relocated/weights.safetensors').open('ab') as stream:
        stream.write(b'x')
    with pytest.raises(ValueError,match='bytes'):
        load_inference_weights(tmp_path/'relocated',target,{'case':'artificial'})
