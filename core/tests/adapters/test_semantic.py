import json
import socket
from unittest.mock import patch

import numpy as np
import pytest

from hts_core.adapters.semantic import REVISION, ResourceUnavailable, SemanticEncoder, cache_path
from hts_core.domain.hybrid import content_windows


@pytest.fixture(scope='module')
def encoder():
    def forbidden(*args, **kwargs):
        raise AssertionError('rede após preparo do cache')
    with patch.object(socket.socket, 'connect', forbidden):
        return SemanticEncoder()


def test_model_missing_is_explicit(tmp_path):
    with pytest.raises(ResourceUnavailable):
        SemanticEncoder(tmp_path)


def test_real_revision_dimension_and_one_window_offline(encoder, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('rede durante inferência')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    text = 'A pesquisa compara dois arquivos em português.'
    actual, info = encoder.encode([text])
    expected = encoder.model.encode([text], normalize_embeddings=True, show_progress_bar=False)
    assert encoder.identity['revision'] == REVISION
    assert encoder.identity['dimension'] == 384
    assert encoder.limit == 128
    assert encoder.capacity + encoder.special == encoder.limit
    assert actual.shape == (1, 384) and np.isfinite(actual).all()
    np.testing.assert_allclose(actual, expected, atol=2e-6, rtol=2e-5)
    assert info[0]['windows'] == 1
    assert info[0]['covered_tokens'] == info[0]['content_tokens']


def test_long_sentence_complete_ids_and_meaningful_tail(encoder):
    text = ('O documento descreve uma experiência de pesquisa controlada ' * 35) + 'Conclusão: o resultado exige revisão.'
    ids = encoder.tokens(text)
    chunks = content_windows(ids, encoder.capacity)
    assert len(chunks) > 1
    assert [token for chunk in chunks for token in chunk] == ids
    assert ids[-5:] == chunks[-1][-5:]
    vectors, info = encoder.encode([text])
    assert info[0]['covered_tokens'] == len(ids)
    assert sum(info[0]['window_tokens']) == len(ids)
    assert max(info[0]['window_tokens']) + encoder.special <= encoder.limit
    assert vectors.shape == (1, 384) and np.isfinite(vectors).all()
    assert np.linalg.norm(vectors[0]) == pytest.approx(1)
    with pytest.raises(ValueError):
        encoder.encode([text], max_tokens=1)


def test_cache_manifest_matches_fixed_configs():
    descriptor = json.loads((cache_path() / 'hts-model.json').read_text())
    assert descriptor['revision'] == REVISION
    config = json.loads((cache_path() / 'sentence_bert_config.json').read_text())
    assert config['max_seq_length'] == 128
