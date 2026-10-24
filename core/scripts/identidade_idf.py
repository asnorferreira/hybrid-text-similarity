"""Proposta de identidade complementar; não constrói nem substitui o IDF histórico."""

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import unicodedata
from pathlib import Path

SCHEMA = "hts-idf-identity-proposal-v2"
CORE = Path(__file__).resolve().parents[1]


def canonical_bytes(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def digest(value: dict) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def describe() -> dict:
    from hts_core.adapters.nlp import SPACY_MODEL, STOPWORDS, model_info
    from hts_core.adapters.refcorpus import manifest_hash, sha256_text
    from hts_core.domain.preprocess import MIN_TOKEN_LENGTH

    corpus = CORE / "data" / "refcorpus"
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    table = json.loads((corpus / "idf.json").read_text(encoding="utf-8"))
    if table["version"] != manifest_hash(manifest):
        raise ValueError("Versão histórica não confere com a projeção do manifesto")
    if table["n_docs"] != len(manifest["documents"]):
        raise ValueError("N não confere com o manifesto")
    if any(type(df) is not int or not 0 < df <= table["n_docs"] for df in table["df"].values()):
        raise ValueError("Frequência documental inválida")
    for entry in manifest["documents"]:
        if sha256_text((corpus / entry["file"]).read_text(encoding="utf-8")) != entry["sha256"]:
            raise ValueError(f"Hash raw divergente: {entry['file']}")
    model_root = Path(importlib.util.find_spec(SPACY_MODEL).origin).parent
    assets = {p.relative_to(model_root).as_posix(): file_hash(p)
              for p in sorted(model_root.rglob("*"))
              if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    sources = ["adapters/refcorpus.py", "adapters/nlp.py", "domain/text.py",
               "domain/preprocess.py", "domain/lexical.py", "cli/__main__.py"]
    files = ["pyproject.toml", "uv.lock", ".python-version", "scripts/identidade_idf.py",
             "configs/refcorpus_provisorio.yaml"]
    payload = {
        "schema": SCHEMA,
        "provenance_status": "observed_artifact_with_current_pipeline_not_attested_build",
        "historical_version": table["version"],
        "corpus_manifest": manifest,
        "idf_table_sha256": file_hash(corpus / "idf.json"),
        "df_content_sha256": digest({"n_docs": table["n_docs"], "df": table["df"]}),
        "table_metadata": {key: value for key, value in table.items() if key != "df"},
        "sources_sha256": {name: file_hash(CORE / "src" / "hts_core" / name) for name in sources},
        "configuration_files_sha256": {name: file_hash(CORE / name) for name in files},
        "processing": {
            "stages": ["wikitext_to_text", "clean_extracted", "lexical_tokens", "document_frequencies"],
            "document_unit": "one Wikipedia revision per document; not sentences",
            "min_token_length": MIN_TOKEN_LENGTH,
            "stopwords": sorted(STOPWORDS),
            "spacy_disabled": ["parser", "ner"],
            "idf": "ln((1+N)/(1+df))+1; unknown term df=0",
            "tf": "raw counts; no vector normalization before cosine",
        },
        "model": {"metadata": model_info(), "assets_sha256": assets},
        "environment": {
            "python": platform.python_version(), "implementation": platform.python_implementation(),
            "unicode": unicodedata.unidata_version,
            "packages": {name: importlib.metadata.version(name) for name in
                         ["spacy", "pt-core-news-sm", "mwparserfromhell", "numpy", "thinc"]},
        },
    }
    return {
        "identity_proposal": digest(payload), "payload": payload,
        "checks": {"raw_hashes_match": True, "historical_version_matches": True,
                   "df_recomputed": False, "historical_build_provenance_confirmed": False},
        "canonicalization": "UTF-8, no BOM; JSON sorted keys, separators comma/colon, ensure_ascii=false, allow_nan=false; arrays retain order",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = describe()
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"identity_proposal": report["identity_proposal"],
                      "historical_version": report["payload"]["historical_version"],
                      "checks": report["checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
