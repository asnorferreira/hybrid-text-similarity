import json
import math
from pathlib import Path

import pytest

from hts_core.adapters.nlp import STOPWORDS, analyze, model_info
from hts_core.adapters.refcorpus import (
    load_idf, manifest_hash, restore_corpus, sha256_text, wikitext_to_text,
)
from hts_core.application.text_pipeline import prepare_sentences
from hts_core.domain.lexical import cosine
from hts_core.domain.preprocess import lexical_tokens
from hts_core.domain.text import clean_extracted

CORPUS = Path(__file__).resolve().parents[2] / "data" / "refcorpus"

pytestmark = pytest.mark.integration


def test_spacy_model_is_the_pinned_one():
    assert model_info() == {"name": "pt_core_news_sm", "version": "3.8.0", "license": "CC BY-SA 4.0"}


def test_lexical_profile_with_real_lemmatizer():
    tokens = lexical_tokens("As meninas estavam correndo pelos jardins floridos.", analyze, STOPWORDS)
    assert "menina" in tokens and "jardim" in tokens
    assert all(len(t) >= 3 and t.isalpha() and t not in STOPWORDS for t in tokens)
    assert "as" not in tokens and "pelos" not in tokens


def test_inflected_forms_share_lemmas():
    a = lexical_tokens("A menina correu pelo jardim.", analyze, STOPWORDS)
    b = lexical_tokens("As meninas correram pelos jardins.", analyze, STOPWORDS)
    assert set(a) == set(b)


def test_prepare_sentences_profiles():
    sentences = prepare_sentences("O rio corre. As pedras rolam no rio.", analyze, STOPWORDS)
    assert [s.raw for s in sentences] == ["O rio corre.", "As pedras rolam no rio."]
    assert [s.words for s in sentences] == [3, 5]
    assert "pedra" in sentences[1].lexical


RAW_MISSING = not (CORPUS / "raw").is_dir()


@pytest.mark.skipif(RAW_MISSING, reason="raw/ fora do Git; rodar restaurar-corpus antes (TCC/11)")
def test_frozen_corpus_files_match_manifest():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["documents"]:
        assert sha256_text((CORPUS / entry["file"]).read_text(encoding="utf-8")) == entry["sha256"]


def test_idf_table_version_is_manifest_hash():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    table = json.loads((CORPUS / "idf.json").read_text(encoding="utf-8"))
    assert table["version"] == manifest_hash(manifest)
    assert table["n_docs"] == len(manifest["documents"])
    assert table["status"] == "provisorio"


def test_reference_idf_identical_documents_are_not_null_vectors():
    idf = load_idf(CORPUS / "idf.json")
    tokens = lexical_tokens(clean_extracted("O Brasil exporta café e soja."), analyze, STOPWORDS)
    vector = idf.vector(tokens)
    assert all(weight >= 1.0 for weight in vector.values())
    assert cosine(vector, idf.vector(list(tokens))) == pytest.approx(1.0)
    assert idf("termoquenãoexiste") == pytest.approx(math.log(1 + idf.n_docs) + 1)


def test_manifest_has_license_and_attribution():
    manifest = json.loads((CORPUS / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["license"] == "CC BY-SA 4.0" and "CC BY-SA 4.0" in manifest["attribution"]
    assert "slots.main.content" in manifest["extraction"]["hash_content"]
    assert "mwparserfromhell 0.7.2" in manifest["extraction"]["text_conversion"]
    for entry in manifest["documents"]:
        assert entry["url"] == f"https://pt.wikipedia.org/w/index.php?oldid={entry['revid']}"
        assert entry["title"] and entry["history_url"].endswith("action=history")


def _fake_fetch(wikitext):
    def fetch(params):
        return {"query": {"pages": [{"title": "T", "pageid": 7, "revisions": [
            {"revid": int(params["revids"]), "timestamp": "2026-01-01T00:00:00Z",
             "slots": {"main": {"content": wikitext}}}]}]}}
    return fetch


def _manifest(tmp_path, wikitext):
    entry = {"title": "T", "revid": 99, "pageid": 7, "file": "raw/7.wiki", "sha256": sha256_text(wikitext)}
    (tmp_path / "manifest.json").write_text(json.dumps({"documents": [entry]}), encoding="utf-8")


def test_restore_by_oldid_writes_file_when_hash_matches(tmp_path):
    _manifest(tmp_path, "texto original")
    assert restore_corpus(tmp_path, fetch=_fake_fetch("texto original"), pause_s=0) == 1
    assert (tmp_path / "raw" / "7.wiki").read_text(encoding="utf-8") == "texto original"


def test_restore_by_oldid_refuses_changed_content(tmp_path):
    _manifest(tmp_path, "texto original")
    with pytest.raises(ValueError, match="hash não confere"):
        restore_corpus(tmp_path, fetch=_fake_fetch("texto alterado"), pause_s=0)
    assert not (tmp_path / "raw" / "7.wiki").exists()


def test_restore_refuses_wrong_revision_identity_even_if_content_matches(tmp_path):
    _manifest(tmp_path, "texto original")
    def fetch(params):
        payload = _fake_fetch("texto original")(params)
        payload["query"]["pages"][0]["revisions"][0]["revid"] = 98
        return payload
    with pytest.raises(ValueError, match="identidade da revisão"):
        restore_corpus(tmp_path, fetch=fetch, pause_s=0)
    assert not (tmp_path / "raw" / "7.wiki").exists()


def test_wikitext_to_text_drops_refs_files_and_markup():
    wikitext = ("'''Brasil''' é um [[país]]<ref>Fonte {{cite|x}}</ref> da [[América do Sul|América]]. "
                "[[Ficheiro:x.png|thumb|legenda]] [[Categoria:Países]]")
    assert wikitext_to_text(wikitext).split() == ["Brasil", "é", "um", "país", "da", "América."]
