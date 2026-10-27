import subprocess
import sys
import tracemalloc

import pytest
import torch
from torch import nn

from hts_core.adapters.training_runtime import (
    file_hash,
    load_training_checkpoint,
    parameters_are_finite,
    save_training_checkpoint,
)
from hts_core.domain.strings import damerau_levenshtein_distance


def test_health_does_not_import_inference_libraries():
    code = """
import sys
from hts_core.adapters.http import create_app
response = create_app().test_client().get('/v1/health')
assert response.status_code == 200
assert not {'torch', 'spacy', 'sentence_transformers', 'pdfplumber', 'docx', 'numpy'} & sys.modules.keys()
"""
    subprocess.run([sys.executable, '-c', code], check=True, capture_output=True, text=True)


def test_osa_peak_allocation_is_bounded_by_rows():
    tracemalloc.start()
    try:
        assert damerau_levenshtein_distance('abcd' * 75, 'badc' * 75) == 150
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 128 * 1024
    assert damerau_levenshtein_distance('CA', 'ABC') == 3


@pytest.mark.parametrize('bad_index', [0, 7, 8, 15, 16, 34])
@pytest.mark.parametrize('bad_value', [float('nan'), float('inf'), -float('inf')])
def test_finiteness_covers_chunk_boundaries_tail_and_frozen_parameters(bad_index, bad_value):
    parameter = nn.Parameter(torch.ones(35), requires_grad=False)
    parameter[bad_index] = bad_value
    assert not parameters_are_finite([torch.ones(2), parameter], chunk_elements=8)
    assert parameter.grad is None


def test_finiteness_uses_bounded_views_for_noncontiguous_weights(monkeypatch):
    parameter = nn.Parameter(torch.arange(315.).reshape(7, 9, 5).transpose(0, 2))
    parameter.sum().backward()
    assert parameter.grad is not None
    gradient = parameter.grad.clone()
    sizes = []
    original = torch.isfinite
    def observe(value):
        sizes.append(value.numel())
        return original(value)
    monkeypatch.setattr(torch, 'isfinite', observe)
    assert not parameter.is_contiguous()
    assert parameters_are_finite([parameter], chunk_elements=8)
    assert sum(sizes) == parameter.numel() and max(sizes) <= 8
    torch.testing.assert_close(parameter.grad, gradient, rtol=0, atol=0)
    with torch.no_grad():
        parameter[-1, -1, -1] = float('inf')
    assert not parameters_are_finite([parameter], chunk_elements=8)


@pytest.mark.parametrize('chunk', [0, -1, True, 1.5])
def test_finiteness_rejects_invalid_chunk_limits(chunk):
    with pytest.raises(ValueError):
        parameters_are_finite([torch.ones(2)], chunk_elements=chunk)


def test_finiteness_handles_empty_and_scalar_tensors():
    assert parameters_are_finite([torch.empty(0), torch.tensor(1.)])
    assert not parameters_are_finite([torch.tensor(float('nan'))])


def test_mapped_optimizer_updates_do_not_change_checkpoint_bytes(tmp_path):
    model = nn.Linear(2, 1)
    optimizer = torch.optim.Adam(model.parameters(), lr=.1)
    def update():
        model(torch.ones(1, 2)).square().sum().backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
    update()
    path = tmp_path / 'checkpoint'
    save_training_checkpoint(path, model, optimizer, {'step': 1}, {})
    hashes = {p.name: file_hash(p) for p in path.iterdir()}
    assert load_training_checkpoint(path, model, optimizer, {}) == {'step': 1}
    update()
    assert {p.name: file_hash(p) for p in path.iterdir()} == hashes
    assert load_training_checkpoint(path, model, optimizer, {}) == {'step': 1}
    assert all(state['step'].item() == 1 for state in optimizer.state.values())
