import copy
from typing import Any
import json

import numpy as np
import pytest
from scipy.special import expit
from scipy.stats import spearmanr

from hts_core.application.calibration import derivation_examples, fit_calibration, predict_platt
from hts_core.domain.calibration import calibration_metrics, fit_platt, probabilities, regularized_targets


def rows(groups=3):
    return [dict(id=f'{g}-{i}',component=f'group-{g}',score=.6 if i%2 else .4,target=i%2)
            for g in range(groups) for i in range(20)]


def test_pl01_pl02_pl05_probability_range_and_rank():
    x = np.linspace(0,1,101).tolist()
    p = probabilities(-8.,4.,x)
    assert all(0 < v < 1 for v in p)
    assert all(a < b for a,b in zip(p,p[1:]))
    assert spearmanr(x,p)[0] == pytest.approx(1.,abs=1e-15,rel=0)
    assert all(0 < v < 1 for v in probabilities(-1e308,1e308,[-1e308,0.,1e308]))


def test_pl03_regularized_targets():
    assert regularized_targets(3,5) == (.8,1/7)


def test_pl04_recovers_known_parameters():
    rng = np.random.Generator(np.random.PCG64(20261025))
    x = rng.uniform(0,1,5000)
    y = (rng.uniform(size=5000) < expit(8*x-4)).astype(int)
    result = fit_platt(x.tolist(),y.tolist())
    assert result['A'] == pytest.approx(-8,rel=.1)
    assert result['B'] == pytest.approx(4,rel=.1)


@pytest.mark.parametrize('split',['train','test'])
def test_pl06_refuses_wrong_fit_split(split):
    with pytest.raises(PermissionError):fit_calibration(rows(),split,{'fixture':'pl06'})


def test_pl07_evaluation_is_out_of_fold_with_group_isolation():
    result = fit_calibration(rows(),'validation',{'fixture':'pl07'})
    evaluation = result['evaluation']
    assert evaluation['status'] == 'evaluated_out_of_fold'
    for fold in evaluation['folds']:
        assert not set(fold['fit_ids']) & set(fold['evaluation_ids'])
        assert not set(fold['fit_groups']) & set(fold['evaluation_groups'])
    assert evaluation['metrics']['brier'] < evaluation['raw_metrics']['brier']
    assert evaluation['metrics']['log_loss'] < evaluation['raw_metrics']['log_loss']
    assert sum(b['count'] for b in evaluation['metrics']['bins']) == len(rows())
    assert result['fit_diagnostics']['scope'] == 'resubstitution_diagnostic_not_independent'


def test_single_component_has_no_independent_metrics():
    result = fit_calibration(rows(1),'validation',{'fixture':'shared'})
    assert result['evaluation']['status'] == 'unavailable'
    assert result['evaluation']['metrics'] is None
    assert 'independent dependency' in result['evaluation']['reason']


def test_pl08_export_roundtrip_and_tamper():
    result = fit_calibration(rows(),'validation',{'fixture':'pl08'})
    original = result['model']; loaded=json.loads(json.dumps(original))
    assert predict_platt(original,[.1,.5,.9]) == predict_platt(loaded,[.1,.5,.9],{'fixture':'pl08'})
    with pytest.raises(ValueError):predict_platt(loaded,[.5],{'fixture':'other'})
    loaded['parameters']['A'] += 1
    with pytest.raises(ValueError):predict_platt(loaded,[.5])


@pytest.mark.parametrize('x,y',[([True],[1]),([float('nan')],[0]),([.5],[True]),([.5,.6],[1,1])])
def test_platt_invalid_inputs(x,y):
    with pytest.raises(ValueError):fit_platt(x,y)


def test_reliability_bins_endpoints_and_empty_bins():
    result=calibration_metrics([0,1],[0.,1.])
    assert result['brier']==0 and result['ece']==0
    assert result['bins'][0]['count']==result['bins'][-1]['count']==1
    assert result['bins'][5]['positive_rate'] is None


def test_provenance_labels_dedup_conflicts_and_closed_test():
    a=dict(id='a',semantic='Uma sentença da fonte.')
    b=dict(id='b',semantic='Outra sentença da fonte.')
    source=dict(id='s',split='validation',sentences=[a,b])
    suspect=dict(id='c',semantic='Sentença transformada.',ancestors=[dict(source_id='s',sentence_id='a')])
    pair=dict(id='p',split='validation',source_ids=['s'],sentences=[suspect])
    data: dict[str, Any] = dict(sources=[source],pairs=[pair,dict(id='test',split='test')],components={'p':'g'})
    examples,counts=derivation_examples(data,'validation')
    assert sorted(r['target'] for r in examples)==[0,1]
    duplicate: dict[str, Any] = copy.deepcopy(pair);duplicate['id']='p2';data['pairs'].append(duplicate);data['components']['p2']='g2'
    examples,counts=derivation_examples(data,'validation')
    assert len(examples)==2 and counts['raw_combinations']==4 and counts['components']==1
    duplicate['sentences'][0]['ancestors']=[]
    examples,counts=derivation_examples(data,'validation')
    assert len(examples)==1 and counts['conflicting_text_pairs_excluded']==1
    with pytest.raises(PermissionError):derivation_examples(data,'test')
