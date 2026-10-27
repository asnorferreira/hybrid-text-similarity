from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Lock

import numpy as np
import pytest
import torch

from hts_core.adapters.semantic import SemanticEncoder
from hts_core.adapters.serving_encoder import ServingEncoder


class Tokenizer:
    special_tokens_map = {'pad_token': '<pad>'}
    model_max_length = 128

    def __len__(self):
        return 12


class Encoder:
    def __init__(self):
        self.model = torch.nn.Linear(2, 2).eval()
        self.model.register_buffer('offset', torch.zeros(1))
        self.tokenizer = Tokenizer()
        self.limit, self.capacity, self.special = 128, 126, 2
        self.identity = {'revision': 'fixture'}
        self.lock = Lock()
        self.calls = []

    def encode(self, texts, max_tokens=12000):
        self.calls.append(list(texts))
        if any(len(text) > max_tokens for text in texts):
            raise ValueError('token budget')
        return np.asarray([[len(text), 1.] for text in texts]), [
            {'content_tokens': len(text), 'windows': 1, 'window_tokens': [len(text)], 'covered_tokens': len(text)}
            for text in texts]


def test_cached_copies_preserve_order_duplicates_and_token_limit():
    base = Encoder()
    serving = ServingEncoder(base)
    expected, info = base.encode(['rio', 'mar', 'rio'])
    base.calls.clear()
    for _ in range(2):
        actual, windows = serving.encode(['rio', 'mar', 'rio'])
        np.testing.assert_array_equal(actual, expected)
        assert windows == info
        actual[0].fill(0)
        windows[0]['window_tokens'].clear()
    assert base.calls == [['rio', 'mar']]
    with pytest.raises(ValueError):
        serving.encode(['rio'], max_tokens=2)


def test_lru_entry_bound_and_expiry():
    base, now = Encoder(), [0.]
    serving = ServingEncoder(base, max_entries=2, ttl=10, clock=lambda: now[0])
    serving.encode(['a', 'b'])
    serving.encode(['a'])
    serving.encode(['c'])
    serving.encode(['a'])
    assert base.calls == [['a', 'b'], ['c']]
    serving.encode(['b'])
    assert base.calls[-1] == ['b']
    now[0] = 10
    serving.encode(['b'])
    assert base.calls[-2:] == [['b'], ['b']]


def test_payload_bound_and_oversized_entries_are_not_retained():
    base = Encoder()
    serving = ServingEncoder(base, max_bytes=180)
    serving.encode(['a', 'b'])
    assert len(serving._cache) == 1 and serving._bytes <= 180
    serving.encode(['a' * 200])
    serving.encode(['a' * 200])
    assert base.calls[-2:] == [['a' * 200], ['a' * 200]]
    assert serving._bytes <= 180


@pytest.mark.parametrize('change', ['weight', 'buffer', 'training', 'tokenizer', 'limit', 'identity', 'dtype'])
def test_changed_serving_state_invalidates_embeddings(change):
    base = Encoder()
    serving = ServingEncoder(base)
    serving.encode(['a'])
    if change == 'weight':
        with torch.no_grad():
            base.model.weight.add_(1)
    elif change == 'buffer':
        base.model.get_buffer('offset').add_(1)
    elif change == 'training':
        base.model.train()
    elif change == 'tokenizer':
        base.tokenizer = Tokenizer()
    elif change == 'limit':
        base.limit -= 1
    elif change == 'identity':
        base.identity = {'revision': 'changed'}
    else:
        base.model.double()
    serving.encode(['a'])
    assert len(base.calls) == 2
    if change == 'training':
        serving.encode(['a', 'a'])
        assert base.calls[-1] == ['a', 'a']
        base.model.eval()
        serving.encode(['a'])
        assert len(base.calls) == 4


def test_autocast_bypasses_cache():
    base = Encoder()
    serving = ServingEncoder(base)
    serving.encode(['a'])
    with torch.autocast('cpu'):
        serving.encode(['a'])
        serving.encode(['a'])
    serving.encode(['a'])
    assert len(base.calls) == 4


def test_concurrent_misses_are_coalesced():
    base = Encoder()
    serving = ServingEncoder(base)
    with ThreadPoolExecutor(max_workers=5) as pool:
        outputs = list(pool.map(lambda _: serving.encode(['rio', 'mar']), range(5)))
    assert base.calls == [['rio', 'mar']]
    for actual, info in outputs:
        np.testing.assert_array_equal(actual, [[3., 1.], [3., 1.]])
        assert info[0]['covered_tokens'] == 3


def test_real_serving_cache_is_bitwise_equal_for_single_and_multiple_windows():
    base = SemanticEncoder()
    serving = ServingEncoder(base)
    texts = ['A pesquisa usa memória limitada.', 'Uma pesquisa controlada mede resultados reais. ' * 35]
    expected, windows = base.encode(texts)
    original = deepcopy(windows)
    calls = []
    hook = base.model.register_forward_hook(lambda *args: calls.append(1))
    try:
        for _ in range(2):
            actual, info = serving.encode(texts + texts)
            np.testing.assert_array_equal(actual, np.concatenate([expected, expected]))
            assert info == original + original
        assert len(calls) == sum(row['windows'] for row in original)
        with pytest.raises(ValueError):
            serving.encode(texts, max_tokens=1)
    finally:
        hook.remove()
