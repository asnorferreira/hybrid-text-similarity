from pathlib import Path

from safetensors import safe_open
import torch


def load_weights_bounded(path: Path | str, model: torch.nn.Module, chunk_bytes: int = 1024 * 1024):
    if type(chunk_bytes) is not int or chunk_bytes < 1:
        raise ValueError('chunk_bytes must be a positive integer')
    targets = model.state_dict()
    with safe_open(str(path), framework='pt', device='cpu', backend='mmap') as reader:
        if set(reader.keys()) != set(targets):
            raise ValueError('checkpoint weight keys differ from model')
        element_sizes = {}
        for name, target in targets.items():
            if list(target.shape) != reader.get_slice(name).get_shape():
                raise ValueError('checkpoint weight shape differs: ' + name)
            size = reader.get_slice(name)[(slice(0, 1),) * target.ndim].element_size()
            element_sizes[name] = max(target.element_size(), size)

    def as_bytes(value):
        flat = value.reshape(-1)
        if flat.stride(0) != 1:
            flat = flat.clone(memory_format=torch.contiguous_format)
        return flat.view(torch.uint8)

    def copy_slice(name, target, indices, element_size):
        if target.numel() == 0:
            return
        if target.numel() * element_size <= chunk_bytes or target.numel() == 1:
            with safe_open(str(path), framework='pt', device='cpu', backend='mmap') as reader:
                value = reader.get_slice(name)[indices]
                same = target.dtype == value.dtype and torch.equal(as_bytes(target), as_bytes(value))
                if not same:
                    target.copy_(value)
                del value
            return
        axis = next(index for index, length in enumerate(target.shape) if length > 1)
        row_bytes = target.numel() // target.shape[axis] * element_size
        width = max(1, chunk_bytes // row_bytes)
        for start in range(0, target.shape[axis], width):
            length = min(width, target.shape[axis] - start)
            selected = list(indices)
            offset = selected[axis].start or 0
            selected[axis] = slice(offset + start, offset + start + length)
            copy_slice(name, target.narrow(axis, start, length), tuple(selected), element_size)

    with torch.no_grad():
        for name, target in targets.items():
            copy_slice(name, target, (slice(None),) * target.ndim, element_sizes[name])
