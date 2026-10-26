import argparse
import json
import sys
from pathlib import Path

import yaml

CORE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = CORE_DIR / "configs" / "refcorpus_provisorio.yaml"
DEFAULT_CORPUS = CORE_DIR / "data" / "refcorpus"


def _download(args: argparse.Namespace) -> None:
    from hts_core.adapters.refcorpus import download_corpus, manifest_hash

    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if not isinstance(config, dict) or not isinstance(config.get('titles'), list):
        raise ValueError('corpus config requires a titles list')
    manifest = download_corpus(config["titles"], Path(args.out))
    print(f"{len(manifest['documents'])} artigos baixados; versão {manifest_hash(manifest)}")


def _restore(args: argparse.Namespace) -> None:
    from hts_core.adapters.refcorpus import restore_corpus

    restored = restore_corpus(Path(args.corpus), limit=args.limit)
    print(f"{restored} revisões baixadas pelo oldid; hashes conferem com o manifesto")


def _build_idf(args: argparse.Namespace) -> None:
    from hts_core.adapters.nlp import STOPWORDS, analyze, model_info
    from hts_core.adapters.refcorpus import build_idf, save_idf
    from hts_core.domain.preprocess import lexical_tokens
    from hts_core.domain.text import clean_extracted

    corpus = Path(args.corpus)
    table = build_idf(corpus, lambda text: lexical_tokens(clean_extracted(text), analyze, STOPWORDS))
    table["status"] = "provisorio"
    table["spacy_model"] = model_info()
    save_idf(table, corpus / "idf.json")
    print(json.dumps({k: table[k] for k in ("version", "n_docs", "status")} | {"termos": len(table["df"])},
                     ensure_ascii=False))


def main() -> None:
    if sys.argv[1:2] == ['training']:
        from hts_core.cli.training import main as training_main
        training_main(sys.argv[2:])
        return
    if sys.argv[1:2] == ['experiment']:
        from hts_core.cli.experiment import main as experiment_main
        experiment_main(sys.argv[2:])
        return
    if sys.argv[1:2] == ['dataset']:
        from hts_core.cli.dataset import main as dataset_main
        dataset_main(sys.argv[2:])
        return
    parser = argparse.ArgumentParser(prog="hts")
    sub = parser.add_subparsers(required=True)

    download = sub.add_parser("baixar-corpus", help="baixa o corpus de referência da Wikipédia")
    download.add_argument("--config", default=str(DEFAULT_CONFIG))
    download.add_argument("--out", default=str(DEFAULT_CORPUS))
    download.set_defaults(func=_download)

    restore = sub.add_parser("restaurar-corpus", help="baixa de novo pelo oldid do manifesto e confere o hash")
    restore.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    restore.add_argument("--limit", type=int, default=None)
    restore.set_defaults(func=_restore)

    build = sub.add_parser("construir-idf", help="congela a tabela df do corpus de referência")
    build.add_argument("--corpus", default=str(DEFAULT_CORPUS))
    build.set_defaults(func=_build_idf)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
