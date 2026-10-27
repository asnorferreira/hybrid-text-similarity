import copy

import pytest
import torch
from torch import nn

from hts_core.adapters.trainable_siamese import Siamese, WindowEncoder


class CountingModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(5, 3)
        self.dropout = nn.Dropout(.5)
        self.calls = 0

    def forward(self, features):
        self.calls += 1
        return {'sentence_embedding': self.dropout(self.embedding(features['input_ids'])).mean(1)}


def window_encoder(**kwargs):
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from tokenizers.processors import TemplateProcessing
    from transformers import PreTrainedTokenizerFast
    backend = Tokenizer(WordLevel({'[UNK]': 0, '[CLS]': 1, '[SEP]': 2, 'a': 3, 'b': 4}, unk_token='[UNK]'))
    backend.pre_tokenizer = Whitespace()
    backend.post_processor = TemplateProcessing(single='[CLS] $A [SEP]', special_tokens=[('[CLS]', 1), ('[SEP]', 2)])
    tokenizer = PreTrainedTokenizerFast(tokenizer_object=backend, unk_token='[UNK]', cls_token='[CLS]', sep_token='[SEP]')
    encoder = WindowEncoder(CountingModel(), tokenizer, limit=5, **kwargs)
    encoder.requires_grad_(False).eval()
    return encoder


def test_repeated_frozen_input_reuses_embeddings_and_keeps_each_diagnostic():
    encoder = window_encoder()
    with torch.no_grad():
        first = encoder('a b a b a b a')
        second = encoder('a b a b a b a')
        second.zero_()
        third = encoder('a b a b a b a')
    assert encoder.model.calls == 3
    torch.testing.assert_close(first, third, rtol=0, atol=0)
    assert encoder.diagnostics == [{'tokens': 7, 'window_tokens': [3, 3, 1], 'covered': 7}] * 3
    encoder.diagnostics[0]['window_tokens'].clear()
    assert encoder.diagnostics[1]['window_tokens'] == [3, 3, 1]
    assert not torch.is_inference(third)


@pytest.mark.parametrize('change', ['update', 'load', 'replace', 'dtype'])
def test_cache_invalidates_when_weights_change(change):
    encoder = window_encoder()
    with torch.no_grad():
        encoder('a b')
        if change == 'update':
            encoder.model.embedding.weight[3].add_(1)
        elif change == 'load':
            state = copy.deepcopy(encoder.state_dict())
            state['model.embedding.weight'][3].add_(1)
            encoder.load_state_dict(state)
        elif change == 'replace':
            encoder.model.embedding.weight = nn.Parameter(encoder.model.embedding.weight + 1, requires_grad=False)
        else:
            encoder.double()
        actual = encoder('a b')
        assert encoder.model.calls == 2
        encoder.clear_embedding_cache()
        expected = encoder('a b')
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)


@pytest.mark.parametrize('mode', ['training', 'unfreeze', 'autograd', 'inference', 'autocast'])
def test_cache_is_bypassed_for_trainable_stochastic_or_different_precision_execution(mode):
    encoder = window_encoder()
    with torch.no_grad():
        encoder('a')
    if mode == 'training':
        encoder.model.train()
    elif mode == 'unfreeze':
        encoder.requires_grad_(True)
    context = (torch.enable_grad() if mode == 'autograd' else torch.inference_mode() if mode == 'inference'
               else torch.autocast('cpu', dtype=torch.bfloat16) if mode == 'autocast' else torch.no_grad())
    with context:
        encoder('a')
        encoder('a')
    assert encoder.model.calls == 3
    assert not encoder._embedding_cache
    if mode in ('training', 'unfreeze'):
        encoder.requires_grad_(False).eval()
        with torch.no_grad():
            encoder('a')
        assert encoder.model.calls == 4


def test_cache_has_byte_and_entry_limits_with_lru_eviction():
    encoder = window_encoder(cache_entries=2)
    with torch.no_grad():
        for text in ['a', 'b', 'a', 'a b']:
            encoder(text)
        assert list(encoder._embedding_cache) == ['a', 'a b']
        assert encoder._cache_size <= encoder.cache_bytes
        size = encoder._cache_size
        encoder('b')
        assert encoder.model.calls == 4
        encoder.clear_embedding_cache()
        encoder.cache_bytes = size // 2
        for text in ['a', 'b', 'a b']:
            encoder(text)
            assert encoder._cache_size <= encoder.cache_bytes
        encoder.cache_bytes = 1
        encoder('a')
        assert not encoder._embedding_cache and encoder._cache_size == 0


def test_frozen_cache_preserves_head_outputs_gradients_updates_and_rng():
    torch.manual_seed(31)
    cached = Siamese(window_encoder(), dimension=3, hidden=4, train_encoder=False).train()
    uncached = copy.deepcopy(cached)
    uncached.encoder.cache_bytes = 0
    optimizers = [torch.optim.Adam(m.head.parameters(), lr=.01) for m in (cached, uncached)]
    for _ in range(3):
        rng = torch.get_rng_state()
        predictions = []
        gradients = []
        for model, optimizer in zip((cached, uncached), optimizers):
            torch.set_rng_state(rng)
            prediction = model('a b a b', 'b a')
            prediction.square().backward()
            predictions.append(prediction.detach())
            head_gradients = []
            for parameter in model.head.parameters():
                assert parameter.grad is not None
                head_gradients.append(parameter.grad.clone())
            gradients.append(head_gradients)
            assert all(p.grad is None for p in model.encoder.parameters())
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        torch.testing.assert_close(predictions[0], predictions[1], rtol=0, atol=0)
        for first, second in zip(gradients[0], gradients[1]):
            torch.testing.assert_close(first, second, rtol=0, atol=0)
        for name, value in cached.state_dict().items():
            torch.testing.assert_close(value, uncached.state_dict()[name], rtol=0, atol=0)
    assert cached.encoder.model.calls == 3 and uncached.encoder.model.calls == 9
