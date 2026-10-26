import math

import pytest

from hts_core.adapters.training_classifiers_v2 import feature_array
from hts_core.application.controlled_training import _h1_features


def test_producer_bounds_machine_roundoff_before_all_four_systems():
    raw = math.nextafter(1.,math.inf)
    assert raw > 1
    with pytest.raises(ValueError):feature_array('lexical',[raw])
    with pytest.raises(ValueError):feature_array('learned_fusion',[[raw,1.]])
    values = _h1_features(raw,raw,True)
    assert values == dict(lexical=1.,semantic=1.,fixed_fusion=1.,learned_fusion=[1.,1.])
    for system,value in values.items():
        assert feature_array(system,[value]).shape[0] == 1


@pytest.mark.parametrize('lexical,semantic',[(1+2e-12,.5),(-2e-12,.5),(.5,1+2e-12),(.5,float('nan'))])
def test_producer_rejects_actual_invalid_scores(lexical,semantic):
    with pytest.raises(ValueError):_h1_features(lexical,semantic,True)


def test_semantic_raw_and_operational_features_stay_distinct():
    assert _h1_features(.25,-.5,True) == dict(lexical=.25,semantic=-.5,fixed_fusion=.1,learned_fusion=[.25,0.])
    assert set(_h1_features(.25,-.5,False)) == {'lexical','semantic','fixed_fusion'}
