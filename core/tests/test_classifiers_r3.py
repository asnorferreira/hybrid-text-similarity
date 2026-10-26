import copy
import json
from pathlib import Path

import numpy as np
import pytest

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.training_classifiers import fit_classifiers, predict_export, save_fitted_classifiers

SPEC=read_json(Path(__file__).resolve().parents[1]/'configs/experiment_s5b.r3.json')['h1']


def examples():
    corners=[(.05,.05),(.05,.95),(.95,.05),(.95,.95)]
    x=[list(v) for v in corners for _ in range(16)]
    y=[c for c in SPEC['classes'] for _ in range(16)]
    features={'lexical':[v[0] for v in x],'semantic':[v[1] for v in x],
              'fixed_fusion':[.4*v[0]+.6*v[1] for v in x],'learned_fusion':x}
    return features,y


def test_rl01_rl02_rl05_rl06_portable_deterministic_separable(tmp_path):
    x,y=examples()
    a=fit_classifiers(x,x,y,y,SPEC,{'fixture':'rl'})
    b=fit_classifiers(x,x,y,y,SPEC,{'fixture':'rl'})
    assert a['learned_fusion']['validation']['accuracy']==1
    assert np.asarray(a['learned_fusion']['model']['coefficients']).shape==(4,2)
    paths=save_fitted_classifiers(a,tmp_path/'exports',{'fixture':'rl'})
    for system in a:
        np.testing.assert_allclose(a[system]['model']['coefficients'],b[system]['model']['coefficients'],atol=1e-12,rtol=0)
        loaded=read_json(tmp_path/'exports'/paths[system]['path'])
        assert loaded['schema']=='hts-logistic-2'
        assert predict_export(json.loads(json.dumps(loaded)),x[system])==a[system]['predictions']
        assert np.isfinite(loaded['coefficients']).all()


@pytest.mark.parametrize('feature',['r','origin','class','source_id','transformation'])
def test_rl03_forbidden_features_refused(feature):
    spec=copy.deepcopy(SPEC);spec['features_by_system']['learned_fusion'][0]=feature
    x,y=examples()
    with pytest.raises(ValueError):fit_classifiers(x,x,y,y,spec,{'fixture':'rl03'})


def test_rl04_missing_class_refused():
    x,y=examples();y=[SPEC['classes'][0] if v==SPEC['classes'][2] else v for v in y]
    with pytest.raises(ValueError,match='every class'):fit_classifiers(x,x,y,y,SPEC,{'fixture':'rl04'})


def test_two_baselines_same_eligible_rows_and_portable(tmp_path):
    from hts_core.adapters.training_baselines import fit_baselines,predict_baseline,save_baselines
    from hts_core.domain.experiments import ModelInput
    x,y=examples()
    values={s:[dict(input=ModelInput('Texto de origem.','Texto de origem.'),target=t) for t in y] for s in ('train','validation')}
    features={s:x for s in values}
    results=fit_baselines(values,features,{'fixture':'baselines'})
    paths=save_baselines(results,tmp_path,{'fixture':'baselines'})
    assert set(results)=={'baseline_q5v2','baseline_majority'}
    for system,result in results.items():
        assert result['validation']['n']==len(y)
        loaded=read_json(tmp_path/paths[system]['path'])
        assert predict_baseline(loaded,values['validation'],x,{'fixture':'baselines'})==result['validation_predictions']
    assert set(results['baseline_q5v2']['validation_predictions'])=={'copia_exata'}
    assert set(results['baseline_majority']['validation_predictions'])=={SPEC['classes'][0]}
