import pytest
from safetensors.torch import load_file, save_file
import torch
from torch import nn

from hts_core.adapters.tensor_storage import load_weights_bounded
from hts_core.adapters.training_runtime import file_hash
from hts_core.adapters import tensor_storage


class Weights(nn.Module):
    scalar: torch.Tensor
    empty: torch.Tensor
    mask: torch.Tensor

    def __init__(self):
        super().__init__()
        self.matrix = nn.Parameter(torch.arange(315.).reshape(7, 9, 5).transpose(0, 2))
        self.register_buffer('scalar', torch.tensor(7, dtype=torch.int64))
        self.register_buffer('empty', torch.empty(0, 3))
        self.register_buffer('mask', torch.tensor([True, False]))


def test_bounded_reload_matches_standard_loader_and_preserves_objects(tmp_path):
    source = Weights()
    path = tmp_path / 'weights.safetensors'
    save_file({name: value.contiguous() for name, value in source.state_dict().items()}, path)
    expected = Weights()
    expected.load_state_dict(load_file(path), strict=True)
    actual = Weights()
    identities = [id(p) for p in actual.parameters()]
    with torch.no_grad():
        actual.matrix.zero_()
        actual.scalar.zero_()
        actual.mask.logical_not_()
    digest = file_hash(path)
    load_weights_bounded(path, actual, chunk_bytes=8)
    assert identities == [id(p) for p in actual.parameters()]
    for name, value in expected.state_dict().items():
        torch.testing.assert_close(actual.state_dict()[name], value, rtol=0, atol=0)
    assert file_hash(path) == digest
    assert actual.matrix.grad is None


def test_unchanged_mapped_weights_remain_shared_with_source_file(tmp_path):
    path = tmp_path / 'weights.safetensors'
    save_file({'weight': torch.arange(64.).reshape(8, 8)}, path)
    model = nn.Linear(8, 8, bias=False)
    model.load_state_dict(load_file(path), assign=True)
    pointer = model.weight.data_ptr()
    version = model.weight._version
    load_weights_bounded(path, model, chunk_bytes=16)
    assert model.weight.data_ptr() == pointer
    assert model.weight._version == version
    with torch.no_grad():
        model.weight[-1, -1] = -1
    load_weights_bounded(path, model, chunk_bytes=16)
    assert model.weight[-1, -1] == 63


def test_reload_preserves_signed_zero_and_nan_payload_bytes(tmp_path):
    model = nn.Module()
    model.register_buffer('value', torch.tensor([0., float('nan')]))
    value = torch.tensor([-2147483648, 2143289345], dtype=torch.int32).view(torch.float32)
    path = tmp_path / 'weights.safetensors'
    save_file({'value': value}, path)
    load_weights_bounded(path, model, chunk_bytes=4)
    assert torch.equal(model.state_dict()['value'].view(torch.uint8), value.view(torch.uint8))


@pytest.mark.parametrize('bad', ['missing', 'extra', 'shape'])
def test_metadata_conflicts_rejected_before_any_weight_is_modified(tmp_path, bad):
    model = nn.Linear(3, 2)
    initial = {name: p.clone() for name, p in model.state_dict().items()}
    data = {name: torch.zeros_like(p) for name, p in initial.items()}
    if bad == 'missing':
        del data['bias']
    elif bad == 'extra':
        data['extra'] = torch.ones(1)
    else:
        data['weight'] = torch.zeros(3, 2)
    path = tmp_path / 'weights.safetensors'
    save_file(data, path)
    with pytest.raises(ValueError, match='keys|shape'):
        load_weights_bounded(path, model, chunk_bytes=8)
    for name, value in model.state_dict().items():
        torch.testing.assert_close(value, initial[name], rtol=0, atol=0)


@pytest.mark.parametrize('limit', [0, -1, True, 2.5])
def test_invalid_chunk_limit_rejected(limit):
    with pytest.raises(ValueError, match='chunk_bytes'):
        load_weights_bounded('unused', nn.Linear(1, 1), chunk_bytes=limit)


def test_mapping_never_reads_an_oversized_slice_and_closes_between_chunks(tmp_path, monkeypatch):
    model = Weights()
    path = tmp_path / 'weights.safetensors'
    save_file({name: value.contiguous().double() for name, value in model.state_dict().items()}, path)
    original = tensor_storage.safe_open
    reads = []
    opened = []
    active = []

    class ObservedSlice:
        def __init__(self, value):
            self.value = value
        def get_shape(self):
            return self.value.get_shape()
        def __getitem__(self, indices):
            value = self.value[indices]
            reads.append(value.numel() * value.element_size())
            return value

    class ObservedReader:
        def __init__(self, *args, **kwargs):
            assert kwargs['backend'] == 'mmap'
            self.reader = original(*args, **kwargs)
        def __enter__(self):
            assert not active
            active.append(self)
            opened.append(self)
            self.reader.__enter__()
            return self
        def __exit__(self, *args):
            active.remove(self)
            return self.reader.__exit__(*args)
        def keys(self):
            return self.reader.keys()
        def get_slice(self, name):
            return ObservedSlice(self.reader.get_slice(name))

    monkeypatch.setattr(tensor_storage, 'safe_open', ObservedReader)
    load_weights_bounded(path, model, chunk_bytes=16)
    assert reads and max(reads) <= 16
    assert len(opened) > 2 and not active
    for name, value in load_file(path).items():
        torch.testing.assert_close(model.state_dict()[name], value.to(model.state_dict()[name].dtype), rtol=0, atol=0)
