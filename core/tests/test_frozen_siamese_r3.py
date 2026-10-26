import copy
from pathlib import Path

import pytest
import torch
from torch import nn

from hts_core.adapters.dataset_store import read_json
from hts_core.adapters.trainable_siamese import Siamese, validate_parameter_profile
from hts_core.adapters.training_runtime import save_training_checkpoint, load_training_checkpoint


class FixtureEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(4,384)
        self.dropout = nn.Dropout(.5)
        self.grad_modes = []

    def forward(self, text):
        self.grad_modes.append(torch.is_grad_enabled())
        return torch.nn.functional.normalize(self.dropout(self.embedding(torch.tensor(int(text)))),dim=0)


def fixture():
    torch.manual_seed(20261025)
    return Siamese(FixtureEncoder(),train_encoder=False)


def spec():
    return read_json(Path(__file__).resolve().parents[1]/'configs/experiment_s5b.r3.json')['siamese']


def test_frozen_mode_and_exact_adopted_parameter_profile():
    model = fixture().train()
    assert model.training and model.head.training and model.head[3].training
    assert all(not m.training for m in model.encoder.modules())
    profile = validate_parameter_profile(model,spec())
    assert profile['trainable_count'] == 98817
    assert profile['frozen_count'] == 4*384
    model('0','1').backward()
    assert model.encoder.grad_modes == [False,False]
    assert all(p.grad is None for p in model.encoder.parameters())
    model.eval().train()
    assert not model.encoder.training and model.head.training
    wrong = copy.deepcopy(spec()); wrong['trainable_parameters']['head.0.weight'] = [128,769]
    with pytest.raises(ValueError,match='protocol'):validate_parameter_profile(model,wrong)


def test_all_head_tensors_receive_gradients_update_and_reduce_loss():
    model = fixture().train()
    before = {name:p.detach().clone() for name,p in model.named_parameters()}
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],
                                 lr=spec()['learning_rate'],weight_decay=spec()['weight_decay'])
    rng = torch.get_rng_state()
    loss = (model('0','1')-1).square()
    loss.backward()
    for p in model.head.parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.norm() > 0
    optimizer.step(); optimizer.zero_grad(set_to_none=True)
    for name,p in model.named_parameters():
        assert torch.equal(p,before[name]) == (not p.requires_grad)
    torch.set_rng_state(rng)
    with torch.no_grad():after = (model('0','1')-1).square()
    assert after < loss.detach()


def test_rg04_frozen_head_checkpoint_reloads_into_new_instance(tmp_path):
    model = fixture().train()
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=2e-6)
    (model('0','1')-.75).square().backward()
    optimizer.step(); optimizer.zero_grad(set_to_none=True)
    model.eval()
    with torch.no_grad():expected = model('0','1')
    save_training_checkpoint(tmp_path/'checkpoint',model,optimizer,{'fixture':True},{'protocol':'r3-fixture'})
    restored = fixture()
    other = torch.optim.Adam([p for p in restored.parameters() if p.requires_grad],lr=2e-6)
    assert load_training_checkpoint(tmp_path/'checkpoint',restored,other,{'protocol':'r3-fixture'}) == {'fixture':True}
    restored.eval()
    with torch.no_grad():observed = restored('0','1')
    torch.testing.assert_close(observed,expected,rtol=0,atol=1e-6)
    assert all(not p.requires_grad and p.grad is None for p in restored.encoder.parameters())
