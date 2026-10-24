from dataclasses import asdict

import numpy as np

from hts_core.application.text_pipeline import prepare_sentences
from hts_core.domain.hybrid import (bounded, class_summary, classify_pair, fuse, hungarian,
                                    semantic_cosine, similarity_index)
from hts_core.domain.lexical import cosine
from hts_core.domain.signature import salient_terms, signature
from hts_core.domain.strings import CHARACTER_ALGORITHMS, levenshtein, vsm_cosine
from hts_core.domain.text import clean_extracted


class InvalidDocument(ValueError):
    pass


class ComparisonService:
    def __init__(self, idf, idf_info, encoder, config, config_sha256, analyze, stopwords, semantic_error=None):
        self.idf, self.idf_info, self.encoder = idf, idf_info, encoder
        self.config, self.config_sha256 = config, config_sha256
        self.analyze, self.stopwords, self.semantic_error = analyze, stopwords, semantic_error

    def _prepare(self, text):
        if len(text) > self.config['max_characters']:
            raise InvalidDocument('limite de caracteres excedido')
        sentences = prepare_sentences(clean_extracted(text), self.analyze, self.stopwords)
        if not sentences or not sum(s.words for s in sentences):
            raise InvalidDocument('documento sem conteúdo útil/peso de palavras')
        if len(sentences) > self.config['max_sentences'] or any(len(s.semantic) > self.config['max_sentence_characters'] for s in sentences):
            raise InvalidDocument('limite de sentenças ou caracteres por sentença excedido')
        return sentences

    def compare(self, source, suspect, mode='hybrid'):
        a, b = self._prepare(source), self._prepare(suspect)
        av, bv = [[self.idf.vector(s.lexical) for s in doc] for doc in (a, b)]
        lexical = np.asarray([[bounded(cosine(x, y)) for y in bv] for x in av])
        wa, wb = [s.words for s in a], [s.words for s in b]
        lexical_index = similarity_index(lexical, wa, wb)
        info = []
        for sentences, vectors in ((a, av), (b, bv)):
            info.append([{**asdict(s), 'lexical': list(s.lexical), 'flags': [] if vector else ['lexical_zero_vector'], 'window': None}
                         for s, vector in zip(sentences, vectors)])
        signatures = []
        for doc in (a, b):
            terms = salient_terms(self.idf.vector(t for s in doc for t in s.lexical))
            signatures.append({'terms': terms, 'value': str(signature(terms))})
        result = {'contract_version': '1.0', 'state': 'calculated', 'method': mode, 'index': None,
                  'lexical_index': lexical_index, 'semantic_index': None,
                  'matrices': {'lexical': lexical.tolist(), 'semantic_raw': None, 'semantic_operational': None, 'fused': None},
                  'source': info[0], 'suspect': info[1], 'matches': None, 'alignment': None, 'summary': None,
                  'metadata': {'policy': 'q5-v2', 'config_sha256': self.config_sha256, 'configuration': self.config,
                               'idf': self.idf_info, 'model': self.encoder.identity if self.encoder else None,
                               'semantic_unavailable': self.semantic_error,
                               'unavailable_components': ['siamese', 'learned_fusion', 'inserted_segment'],
                               'signature': {'method': 'adapted_top30_tfidf_set_blake2b64_mod2^64', 'source': signatures[0],
                                             'suspect': signatures[1], 'equal_is_not_identity': True}}}
        if mode == 'lexical':
            result['index'] = lexical_index
            return result
        if self.encoder is None:
            result['state'] = 'resource_unavailable'
            return result
        vectors, windows = self.encoder.encode([s.semantic for s in a + b], self.config['max_content_tokens'])
        for i, item in enumerate(info[0] + info[1]):
            item['window'] = windows[i]
        semantic = np.asarray([[semantic_cosine(x, y) for y in vectors[len(a):]] for x in vectors[:len(a)]])
        operational, fused = fuse(lexical, semantic)
        result['index'] = similarity_index(fused, wa, wb)
        result['semantic_index'] = similarity_index(operational, wa, wb)
        result['matrices'].update(semantic_raw=semantic.tolist(), semantic_operational=operational.tolist(), fused=fused.tolist())
        result['alignment'] = hungarian(fused)
        matches = []
        thresholds = {name: self.config[name] for name in ('edited_threshold', 'low_threshold', 'paraphrase_threshold', 'lexical_high')}
        for j, sentence in enumerate(b):
            i = int(np.argmax(fused[:, j]))
            x, y = a[i].semantic, sentence.semantic
            edit = levenshtein(x, y)
            characters = {name: func(x, y) for name, func in CHARACTER_ALGORITHMS.items()}
            characters['osa'] = characters.pop('damerau_levenshtein')
            characters['vsm_cosine'] = vsm_cosine(a[i].lexical, sentence.lexical)
            decision = classify_pair(x, y, lexical[i, j], operational[i, j], edit, **thresholds)
            matches.append({'source': i, 'suspect': j, 'lexical': float(lexical[i, j]), 'semantic_raw': float(semantic[i, j]),
                            'semantic_operational': float(operational[i, j]), 'fused': float(fused[i, j]),
                            'edit': edit, 'characters': characters, 'decision': decision})
        result['matches'] = matches
        result['summary'] = class_summary([m['decision']['label'] for m in matches])
        return result
