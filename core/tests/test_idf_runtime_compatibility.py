from copy import deepcopy

import pytest

from hts_core.adapters.idf_contract import runtime_lexical_compatibility
from tests.test_experiment_preparation import fixture_pipeline


def test_global_lock_difference_is_explicit_and_never_full_environment_equivalence():
    before=fixture_pipeline();after=deepcopy(before);after['lock_sha256']='1'*64
    with pytest.raises(ValueError,match='produtor'):
        runtime_lexical_compatibility(before,after)
    result=runtime_lexical_compatibility(before,after,True)
    assert result['identical'] is False and result['different_lock_explicitly_permitted'] is True
    assert result['sealed']=='0'*64 and result['runtime']=='1'*64
    assert 'full df recomputation still required' in result['scope']


@pytest.mark.parametrize('change',['code','assets','package','stopwords','python'])
def test_lock_permission_never_accepts_changed_lexical_dependencies(change):
    before=fixture_pipeline();after=deepcopy(before);after['lock_sha256']='1'*64
    if change=='code':after['code']['domain/preprocess.py']='2'*64
    elif change=='assets':after['model_assets']['new']='2'*64
    elif change=='package':after['packages']['spacy']='different'
    elif change=='stopwords':after['stopwords'].append('artificial')
    else:after['python']='0.0.0'
    with pytest.raises(ValueError,match='produtor'):
        runtime_lexical_compatibility(before,after,True)


def test_numeric_permission_rejected():
    with pytest.raises(ValueError,match='boolean'):
        runtime_lexical_compatibility(fixture_pipeline(),fixture_pipeline(),1)
