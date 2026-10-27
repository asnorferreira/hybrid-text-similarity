"""Bounded memoization of the immutable serving NLP pipeline's output."""
from collections import OrderedDict
from threading import Lock
from time import monotonic


class ServingAnalysis:
    def __init__(self, analyze, *, max_entries=256, max_bytes=2 * 1024 * 1024, ttl=300, clock=monotonic):
        if max_entries < 1 or max_bytes < 1 or ttl <= 0:
            raise ValueError('invalid analysis cache limits')
        self.analyze = analyze
        self.max_entries, self.max_bytes, self.ttl = max_entries, max_bytes, ttl
        self.clock = clock
        self._guard = Lock()
        self._cache = OrderedDict()
        self._bytes = 0
        self._analyzer = analyze

    def __call__(self, text):
        # The HTTP pipeline is fixed for the process lifetime. Replacing the
        # analyzer invalidates cached entries; in-place pipeline edits require
        # a process restart. No cache is attached to scientific runners.
        with self._guard:
            if self.analyze is not self._analyzer:
                self._cache.clear()
                self._bytes = 0
                self._analyzer = self.analyze
            now = self.clock()
            for key, (_, expires, size) in list(self._cache.items()):
                if expires <= now:
                    del self._cache[key]
                    self._bytes -= size
            if text in self._cache:
                values, _, _ = self._cache[text]
                self._cache.move_to_end(text)
                return list(values)
            # Strings and tuples are immutable; callers receive a new list.
            values = tuple((surface, lemma) for surface, lemma in self.analyze(text))
            size = len(text.encode('utf-8')) + sum(len(a.encode('utf-8')) + len(b.encode('utf-8')) for a, b in values)
            if size <= self.max_bytes:
                while self._cache and (len(self._cache) >= self.max_entries or self._bytes + size > self.max_bytes):
                    _, (_, _, removed) = self._cache.popitem(last=False)
                    self._bytes -= removed
                self._cache[text] = values, self.clock() + self.ttl, size
                self._bytes += size
            return list(values)
