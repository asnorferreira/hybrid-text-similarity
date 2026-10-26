import argparse
import hashlib
import json
from pathlib import Path
import sys

CORE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CORE))
from tests.equivalence_support import (
    STRONG,
    client_for,
    make_service,
    projection,
    strong_response,
)
from hts_core.adapters.semantic import cache_path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(out, provenance):
    out = Path(out)
    if out.exists():
        raise FileExistsError("snapshot já existe; preserve-o e use outro destino")
    origin = json.loads(Path(provenance).read_text(encoding="utf-8"))
    if not origin.get("commit") or not origin.get("source_files_sha256"):
        raise ValueError("proveniência exige commit e hashes da árvore de fontes")
    for relative, expected in origin["source_files_sha256"].items():
        if digest(CORE / relative) != expected:
            raise ValueError(f"fonte diverge da proveniência: {relative}")
    service = make_service()
    assert service.encoder is not None
    client = client_for(service)
    cases = [
        dict(
            id=case,
            format=kind,
            mode=mode,
            relation=relation,
            result=projection(strong_response(client, kind, mode, relation)),
        )
        for case, kind, mode, relation in STRONG
    ]
    snapshot = {
        "schema": "hts-q5v2-regression-1",
        "purpose": "software_regression_not_scientific_evaluation",
        "research_dataset_used": False,
        "generation": {
            "script": "scripts/generate_q5v2_snapshot.py",
            "script_sha256": digest(Path(__file__)),
            "command": "python scripts/generate_q5v2_snapshot.py --provenance /provenance.json --out /snapshot/q5v2-snapshot.json",
            "environment": "prepared core Docker image, CPU, offline",
            "provenance": origin,
            "fixtures_manifest_sha256": digest(
                CORE / "tests/fixtures/equivalence/formats/manifest.json"
            ),
        },
        "tolerance": {"absolute": 1e-9, "relative": 0},
        "resources": {
            "model": service.encoder.identity,
            "model_manifest_sha256": digest(cache_path() / "hts-model.json"),
            "application_idf": service.idf_info,
            "policy_file_sha256": service.config["file_sha256"],
            "research_training_idf_used": False,
        },
        "cases": cases,
    }
    data = (
        json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("xb") as stream:
        stream.write(data)
    return {
        "cases": len(cases),
        "sha256": hashlib.sha256(data).hexdigest(),
        "research_dataset_used": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Congelar os 32 casos NFo em uma saída nova."
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(generate(args.out, args.provenance)))
