import os

import pytest
import torch

from hts_core.adapters.training_artifacts import load_inference_weights
from hts_core.adapters.training_runtime import save_training_checkpoint, load_training_checkpoint


@pytest.mark.skipif(os.name == 'nt',reason='real symlink fixture requires Linux Docker; Windows link privilege not assumed')
@pytest.mark.parametrize('loader',['training','inference'])
def test_manifest_leaf_symlink_rejected_before_loading(tmp_path,loader):
    model = torch.nn.Linear(1,1)
    optimizer = torch.optim.Adam(model.parameters())
    bindings = {'case':'artificial'}
    checkpoint = tmp_path/'checkpoint'
    save_training_checkpoint(checkpoint,model,optimizer,{},bindings)
    outside = tmp_path/'outside-manifest.json'
    (checkpoint/'manifest.json').rename(outside)
    (checkpoint/'manifest.json').symlink_to(outside)
    with pytest.raises(ValueError,match='link|reparse'):
        if loader == 'training':
            load_training_checkpoint(checkpoint,model,optimizer,bindings)
        else:
            load_inference_weights(checkpoint,model,bindings)
