import pytest

from tests.test_dataset_s4 import dataset
from hts_core.adapters.dataset_store import canonical, digest, identity, read_json
from hts_core.adapters.dataset_validation import validate_training_idf
from hts_core.adapters.idf_contract import validate_training_idf_contract
from hts_core.application.dataset_pipeline import build_training_idf, pipeline_descriptor


@pytest.mark.integration
def test_explicit_lock_mode_still_recomputes_df_and_rejects_fully_rehashed_corruption(dataset,tmp_path,monkeypatch):
    destination=tmp_path/'idf'
    build_training_idf(dataset,destination)
    runtime=pipeline_descriptor()
    runtime['lock_sha256']='1'*64
    monkeypatch.setattr('hts_core.application.dataset_pipeline.pipeline_descriptor',lambda:runtime)
    with pytest.raises(ValueError,match='produtor'):
        validate_training_idf(dataset,destination)
    good=validate_training_idf(dataset,destination,allow_runtime_lock_difference=True)
    assert good['sources']==14 and good['lexical_recomputation']=='executed'
    assert good['runtime_lock_comparison']['identical'] is False

    table=read_json(destination/'idf.json')
    descriptor=read_json(destination/'construction.json')
    execution=read_json(destination/'execution.json')
    term=next(k for k,v in table['df'].items() if v<table['n_docs'])
    table['df'][term]+=1
    descriptor['table_content_sha256']=identity({k:v for k,v in table.items() if k!='version'})
    descriptor['identity']=identity({k:v for k,v in descriptor.items() if k!='identity'})
    table['version']=descriptor['identity']
    (destination/'idf.json').write_bytes(canonical(table))
    (destination/'construction.json').write_bytes(canonical(descriptor))
    execution['serialized_table_sha256']=digest((destination/'idf.json').read_bytes())
    (destination/'execution.json').write_bytes(canonical(execution))
    assert validate_training_idf_contract(dataset,destination)['integrity']=='verified'
    with pytest.raises(ValueError,match='df do IDF divergente'):
        validate_training_idf(dataset,destination,allow_runtime_lock_difference=True)
