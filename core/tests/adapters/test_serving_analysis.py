from concurrent.futures import ThreadPoolExecutor

import pytest

from hts_core.adapters.serving_analysis import ServingAnalysis


def test_analysis_copies_results_and_coalesces_concurrent_misses():
    calls = []
    def analyze(text):
        calls.append(text)
        return [(text, text.lower())]
    cached = ServingAnalysis(analyze)
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(cached, ['AÇÃO'] * 5))
    assert results == [[('AÇÃO', 'ação')]] * 5
    assert calls == ['AÇÃO']
    results[0].clear()
    assert cached('AÇÃO') == [('AÇÃO', 'ação')]
    assert results[1] == [('AÇÃO', 'ação')]


def test_analysis_lru_expiry_and_analyzer_replacement():
    calls, now = [], [0.]
    def analyze(text):
        calls.append(text)
        return [(text, text)]
    cached = ServingAnalysis(analyze, max_entries=2, ttl=10, clock=lambda: now[0])
    for text in ['a', 'b', 'a', 'c', 'a']:
        cached(text)
    assert calls == ['a', 'b', 'c']
    cached('b')
    assert calls == ['a', 'b', 'c', 'b']
    now[0] = 10
    cached('b')
    assert calls[-2:] == ['b', 'b']
    cached.analyze = lambda text: [(text, 'novo')]
    assert cached('b') == [('b', 'novo')]


def test_analysis_payload_bound_and_oversized_input_not_retained():
    calls = []
    def analyze(text):
        calls.append(text)
        return [(text, text)]
    cached = ServingAnalysis(analyze, max_bytes=3)
    for text in ['a', 'b', 'ab', 'ab']:
        cached(text)
    assert cached._bytes <= 3 and len(cached._cache) <= 1
    assert calls == ['a', 'b', 'ab', 'ab']


def test_analysis_failures_are_not_cached():
    calls = []
    def broken(text):
        calls.append(text)
        raise ValueError('fixture failure')
    cached = ServingAnalysis(broken)
    for _ in range(2):
        with pytest.raises(ValueError):
            cached('text')
    assert len(calls) == 2


def test_real_analysis_is_identical_in_latin_arabic_cjk_and_unicode():
    from hts_core.adapters.nlp import analyze
    cached = ServingAnalysis(analyze)
    for text in ['A pesquisa é válida: ações e resultados.', 'تبحث الدراسة في اللغة العربية.', '研究比较文本相似性。', 'Cafe\u0301 — café.']:
        expected = analyze(text)
        assert cached(text) == expected
        assert cached(text) == expected
