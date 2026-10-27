from collections import OrderedDict
from contextlib import nullcontext
import sys
from typing import TypedDict

import torch
from torch import nn
import torch.nn.functional as F


def pool_tensors(embeddings, counts):
    if not embeddings or len(embeddings) != len(counts) or any(type(c) is not int or c <= 0 for c in counts):
        raise ValueError('nonempty windows with positive content counts required')
    stacked = torch.stack(embeddings)
    weights = stacked.new_tensor(counts)
    return F.normalize((stacked*weights[:,None]).sum(0)/weights.sum(), dim=0)


class WindowEncoder(nn.Module):
    def __init__(self, model, tokenizer, limit, cache_bytes=1024 * 1024, cache_entries=128):
        super().__init__()
        self.model, self.tokenizer, self.limit = model, tokenizer, limit
        self.capacity = limit-tokenizer.num_special_tokens_to_add(pair=False)
        if self.capacity < 1:
            raise ValueError('no room for content')
        if type(cache_bytes) is not int or cache_bytes < 0 or type(cache_entries) is not int or cache_entries < 0:
            raise ValueError('cache limits must be nonnegative integers')
        self.diagnostics = []
        self.cache_bytes, self.cache_entries = cache_bytes, cache_entries
        self._embedding_cache: OrderedDict[str, tuple[torch.Tensor, int, tuple[int, ...], int]] = OrderedDict()
        self._cache_size = 0
        self._cache_signature = None

    def clear_embedding_cache(self):
        self._embedding_cache.clear()
        self._cache_size = 0
        self._cache_signature = None

    def _cache_allowed(self):
        parameters = tuple(self.model.parameters())
        tensors = (*parameters, *self.model.buffers())
        allowed = (self.cache_bytes > 0 and self.cache_entries > 0 and not torch.is_grad_enabled()
                   and not torch.is_inference_mode_enabled() and not torch.is_autocast_enabled('cpu')
                   and not torch.is_autocast_enabled('cuda') and not any(p.requires_grad for p in parameters)
                   and not any(module.training for module in self.model.modules())
                   and not any(torch.is_inference(tensor) for tensor in tensors))
        if not allowed:
            self.clear_embedding_cache()
            return False
        signature = (self.capacity, self.limit, self.cache_bytes, self.cache_entries, id(self.tokenizer),
                     tuple((id(t), t._version, t.dtype, t.device) for t in tensors))
        if signature != self._cache_signature:
            self.clear_embedding_cache()
            self._cache_signature = signature
        return True

    def forward(self, text):
        cache_allowed = self._cache_allowed()
        if cache_allowed and text in self._embedding_cache:
            value, tokens, counts, _ = self._embedding_cache[text]
            self._embedding_cache.move_to_end(text)
            self.diagnostics.append({'tokens': tokens, 'window_tokens': list(counts), 'covered': sum(counts)})
            return value.clone()
        encoded = self.tokenizer(text, add_special_tokens=False, truncation=False).encodings[0]
        original = list(encoded.ids)
        if not original or len(original) > 12000:
            raise ValueError('empty or oversized token input')
        encoded.truncate(self.capacity, stride=0)
        chunks = [encoded, *encoded.overflowing]
        if [x for chunk in chunks for x in chunk.ids] != original:
            raise ValueError('incomplete token coverage')
        embeddings, counts = [], []
        for chunk in chunks:
            prepared = self.tokenizer.backend_tokenizer.post_process(chunk, add_special_tokens=True)
            if len(prepared.ids) > self.limit:
                raise ValueError('window exceeds model limit')
            features = {k:torch.tensor([v], dtype=torch.long) for k,v in (
                ('input_ids',prepared.ids), ('attention_mask',prepared.attention_mask), ('token_type_ids',prepared.type_ids))}
            embeddings.append(self.model(features)['sentence_embedding'][0])
            counts.append(len(chunk.ids))
        self.diagnostics.append({'tokens':len(original), 'window_tokens':counts, 'covered':sum(counts)})
        value = pool_tensors(embeddings, counts)
        if cache_allowed:
            window_counts = tuple(counts)
            size = (sys.getsizeof(text) + value.numel() * value.element_size() + sys.getsizeof(value)
                    + sys.getsizeof(window_counts) + sum(sys.getsizeof(c) for c in counts) + 256)
            if size <= self.cache_bytes:
                while self._embedding_cache and (self._cache_size + size > self.cache_bytes
                                                  or len(self._embedding_cache) >= self.cache_entries):
                    _, evicted = self._embedding_cache.popitem(last=False)
                    self._cache_size -= evicted[3]
                self._embedding_cache[text] = (value.detach().clone(), len(original), window_counts, size)
                self._cache_size += size
        return value


class Siamese(nn.Module):
    def __init__(self, encoder, dimension=384, hidden=128, dropout=.1, alpha=.1, epsilon=1e-5, train_encoder=True):
        super().__init__()
        self.encoder = encoder
        self.train_encoder = train_encoder
        for parameter in encoder.parameters():
            parameter.requires_grad_(train_encoder)
        if not train_encoder:
            encoder.eval()
        self.head = nn.Sequential(nn.Linear(2*dimension, hidden), nn.LayerNorm(hidden,eps=epsilon),
                                  nn.LeakyReLU(alpha), nn.Dropout(dropout), nn.Linear(hidden,1), nn.Sigmoid())

    def train(self, mode=True):
        super().train(mode)
        if not self.train_encoder:
            self.encoder.eval()
        return self

    def forward(self, source_text, suspect_text):
        with nullcontext() if self.train_encoder else torch.no_grad():
            u, v = self.encoder(source_text), self.encoder(suspect_text)
        return self.head(torch.cat((torch.abs(u-v),u*v))).reshape(())


class ParameterInfo(TypedDict):
    shape: list[int]
    count: int


class ParameterProfile(TypedDict):
    trainable: dict[str, ParameterInfo]
    trainable_count: int
    frozen_count: int


def parameter_profile(model) -> ParameterProfile:
    trainable: dict[str, ParameterInfo] = {name:ParameterInfo(shape=list(p.shape),count=p.numel())
                 for name,p in model.named_parameters() if p.requires_grad}
    return ParameterProfile(trainable=trainable,trainable_count=sum(v['count'] for v in trainable.values()),
                frozen_count=sum(p.numel() for p in model.parameters() if not p.requires_grad))


def validate_parameter_profile(model, spec):
    profile = parameter_profile(model)
    if 'trainable_parameters' in spec:
        actual = {name:row['shape'] for name,row in profile['trainable'].items()}
        if actual != spec['trainable_parameters'] or profile['trainable_count'] != spec['trainable_parameter_count']:
            raise ValueError('trainable parameters differ from adopted protocol')
    return profile


def load_local_trainable(config):
    from hts_core.adapters.semantic import SemanticEncoder
    adapter = SemanticEncoder()
    encoder = WindowEncoder(adapter.model, adapter.tokenizer, adapter.limit)
    spec = config['siamese']
    model = Siamese(encoder, spec['embedding_dimension'], spec['dense_dimensions'][1], spec['dropout'],
                    spec['leaky_relu_alpha'], spec['layer_norm_epsilon'], spec['encoder_trainable'])
    validate_parameter_profile(model,spec)
    return model, adapter.identity
