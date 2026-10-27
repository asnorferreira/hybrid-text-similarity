"""Bounded, process-local inference cache; never used by scientific runners.

Only embeddings and window diagnostics are retained, never comparison results.
The serving model/tokenizer must not be modified concurrently with inference.
"""
from collections import OrderedDict
from copy import deepcopy
import json
from threading import Lock
from time import monotonic


class ServingEncoder:
    def __init__(self, encoder, *, max_entries=256, max_bytes=8 * 1024 * 1024, ttl=300, clock=monotonic):
        if max_entries < 1 or max_bytes < 1 or ttl <= 0:
            raise ValueError('invalid serving cache limits')
        self.encoder = encoder
        self.max_entries, self.max_bytes, self.ttl = max_entries, max_bytes, ttl
        self.clock = clock
        self._guard = Lock()
        self._cache = OrderedDict()
        self._bytes = 0
        self._state = None

    def __getattr__(self, name):
        return getattr(self.encoder, name)

    def _signature(self):
        import torch
        model = self.encoder.model
        if any(m.training for m in model.modules()) or torch.is_autocast_enabled('cpu') or torch.is_autocast_enabled('cuda'):
            return None
        tensors = list(model.parameters()) + list(model.buffers())
        if any(t.is_inference() for t in tensors):
            return None
        return (id(model), id(self.encoder.tokenizer), len(self.encoder.tokenizer),
                repr(self.encoder.tokenizer.special_tokens_map), self.encoder.tokenizer.model_max_length,
                self.encoder.limit, self.encoder.capacity, self.encoder.special,
                json.dumps(self.encoder.identity, sort_keys=True),
                tuple((id(t), t._version, t.dtype, t.device, t.requires_grad) for t in tensors))

    def encode(self, texts, max_tokens=12000):
        import numpy as np
        # Serializing cache access also coalesces concurrent misses. The base
        # encoder retains its own lock, shared with the opt-in H2 forward path.
        with self._guard:
            state = self._signature()
            if state is None or state != self._state:
                self._cache.clear()
                self._bytes = 0
                self._state = state
            if state is None or not texts:
                return self.encoder.encode(texts, max_tokens)
            now = self.clock()
            for key, (_, _, expires, size) in list(self._cache.items()):
                if expires <= now:
                    del self._cache[key]
                    self._bytes -= size
            found, missing = {}, []
            for text in dict.fromkeys(texts):
                cached = self._cache.get(text)
                if cached is None:
                    missing.append(text)
                else:
                    vector, info, _, _ = cached
                    if info['content_tokens'] > max_tokens:
                        raise ValueError('limite de tokens de conteúdo excedido')
                    found[text] = vector, info
                    self._cache.move_to_end(text)
            if missing:
                vectors, diagnostics = self.encoder.encode(missing, max_tokens)
                for text, vector, info in zip(missing, vectors, diagnostics, strict=True):
                    vector, info = vector.copy(), deepcopy(info)
                    found[text] = vector, info
                    # This is a retained payload budget; entry count separately
                    # bounds Python container overhead. No text is persisted.
                    size = len(text.encode('utf-8')) + vector.nbytes + len(json.dumps(info).encode('utf-8'))
                    if size > self.max_bytes:
                        continue
                    while self._cache and (len(self._cache) >= self.max_entries or self._bytes + size > self.max_bytes):
                        _, (_, _, _, removed) = self._cache.popitem(last=False)
                        self._bytes -= removed
                    self._cache[text] = vector, info, self.clock() + self.ttl, size
                    self._bytes += size
            return np.asarray([found[text][0] for text in texts]), [deepcopy(found[text][1]) for text in texts]
