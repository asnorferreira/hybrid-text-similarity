from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

CORE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare_s5c_reference', CORE/'scripts/prepare_s5c_reference.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def plan():
    return json.loads((CORE/'configs/reference_s5c.plan.json').read_text())


def data():
    source={'id':'s','split':'test','sentences':[{'id':str(i),'semantic':f'Fonte artificial {i}.'} for i in range(4)]}
    pairs=[{'id':f'p{i}','source_id':'s','split':'test','method':'copy' if i<4 else 'edit','severity':'low',
            'sentences':[{'id':f'b{i}','semantic':f'Frase artificial distinta {i}.','ancestors':[{'source_id':'s','sentence_id':'0'}]}]} for i in range(8)]
    return {'sources':[source],'pairs':pairs}


def test_selection_is_deterministic_and_covers_cells_and_nonancestral():
    first=module.select(data(),plan())
    reversed_data=data();reversed_data['pairs'].reverse();reversed_data['sources'][0]['sentences'].reverse()
    assert module.select(reversed_data,plan())==first
    assert len(first)==6
    assert len({(r['source_text_sha256'],r['suspect_text_sha256']) for r in first})==6
    assert len([r for r in first if r['stratum']=='nonancestral_cross'])==4
    assert all(r['source_sentence_id']!='0' for r in first if r['stratum']=='nonancestral_cross')
    assert {r['stratum'] for r in first if r['stratum']!='nonancestral_cross'}=={"('copy', 'low')","('edit', 'low')"}
    assert all('target' not in r and 'prediction' not in r for r in first)


def test_other_splits_are_not_selected():
    fixture=data();extra=deepcopy(fixture['pairs'][0]);extra.update(id='train-only',split='train')
    fixture['pairs'].append(extra)
    assert all(r['pair_id']!='train-only' for r in module.select(fixture,plan()))


def test_cross_split_source_is_rejected():
    fixture=data();fixture['sources'][0]['split']='train'
    with pytest.raises(ValueError,match='split'):
        module.select(fixture,plan())


def test_no_duplicate_replacement_or_silent_ceiling_expansion():
    limited=plan();limited['maximum_observations']=5
    with pytest.raises(ValueError,match='ceiling'):
        module.select(data(),limited)
    fixture=data()
    for p in fixture['pairs']:p['sentences'][0]['semantic']='mesmo texto artificial'
    with pytest.raises(ValueError,match='duplicates'):
        module.select(fixture,plan())


@pytest.mark.parametrize('field,value',[('seed',True),('test_predictions_authorized',0),('maximum_observations',48),('hidden_score',.8)])
def test_plan_rejects_ignored_fields_and_changed_contract(field,value):
    changed=plan();changed[field]=value
    with pytest.raises(ValueError):module.validate_plan(changed)


def test_plan_check_never_opens_dataset_or_produces_labels(tmp_path,capsys):
    module.main(['--plan',str(CORE/'configs/reference_s5c.plan.json'),'--check-plan-only','--dataset',str(tmp_path/'nonexistent')])
    receipt=json.loads(capsys.readouterr().out)
    assert receipt['status']=='plan_checked_no_dataset_opened'
    assert receipt['labels_produced']==0 and receipt['predictions'] is False
    assert list(tmp_path.iterdir())==[]


def test_preparation_refuses_missing_separate_authorization(tmp_path):
    with pytest.raises(SystemExit) as error:
        module.main(['--plan',str(CORE/'configs/reference_s5c.plan.json'),'--dataset',str(tmp_path/'not-opened'),'--out',str(tmp_path/'out')])
    assert error.value.code==2 and not (tmp_path/'out').exists()
