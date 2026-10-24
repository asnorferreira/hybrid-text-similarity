import copy
import hashlib
import importlib.util
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("idf_identity_proposal", CORE / "scripts" / "identidade_idf.py")
proposal = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(proposal)


def test_canonical_encoding_has_explicit_bytes_and_preserves_array_order():
    assert proposal.canonical_bytes({"b": 2, "a": "ação"}) == '{"a":"ação","b":2}'.encode("utf-8")
    assert proposal.digest({"b": 2, "a": 1}) == hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    assert proposal.digest({"a": [1, 2]}) != proposal.digest({"a": [2, 1]})
    with pytest.raises(ValueError):
        proposal.digest({"x": float("nan")})


@pytest.fixture(scope="module")
def real_descriptor():
    return proposal.describe()


@pytest.mark.parametrize("path", [
    ("configuration_files_sha256", "configs/refcorpus_provisorio.yaml"),
    ("model", "metadata", "version"),
    ("df_content_sha256",),
    ("sources_sha256", "domain/preprocess.py"),
    ("corpus_manifest", "documents", 0, "revid"),
    ("environment", "packages", "spacy"),
])
def test_identity_changes_when_relevant_content_changes(real_descriptor, path):
    changed = copy.deepcopy(real_descriptor["payload"])
    node = changed
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = "altered"
    assert proposal.digest(changed) != real_descriptor["identity_proposal"]


@pytest.mark.integration
def test_real_descriptor_is_repeatable_and_preserves_historical_artifacts(real_descriptor):
    paths = [CORE / "data/refcorpus/manifest.json", CORE / "data/refcorpus/idf.json"]
    before = [path.read_bytes() for path in paths]
    first = real_descriptor
    assert proposal.describe() == first
    assert [path.read_bytes() for path in paths] == before
    assert first["checks"]["raw_hashes_match"]
    assert first["checks"]["df_recomputed"] is False
    assert first["checks"]["historical_build_provenance_confirmed"] is False
    payload = first["payload"]
    assert payload["schema"] == proposal.SCHEMA
    assert payload["model"]["assets_sha256"]
    assert payload["processing"]["stopwords"]
    assert "domain/preprocess.py" in payload["sources_sha256"]
