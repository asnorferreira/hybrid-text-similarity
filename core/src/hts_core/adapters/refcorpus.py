"""Corpus de referência do IDF (guia 0.3): wikitext da Wikipédia em português por revisão (oldid), com manifesto e hash."""

import hashlib
import json
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import mwparserfromhell

from hts_core.domain.lexical import ReferenceIdf, document_frequencies

API = "https://pt.wikipedia.org/w/api.php"
USER_AGENT = "hts-core/0.1 (https://github.com/asnorferreira/hybrid-text-similarity; TCC) python-urllib/3.11"
LICENSE = "CC BY-SA 4.0"
ATTRIBUTION = ("Textos de artigos da Wikipédia em português (pt.wikipedia.org), na revisão indicada por oldid; "
               "autores no histórico de cada artigo (history_url); licença CC BY-SA 4.0.")
EXTRACTION = {
    "raw_format": "MediaWiki wikitext, revision slots.main.content",
    "hash_content": "sha256 of slots.main.content encoded as UTF-8, no BOM or Unicode normalization",
    "storage": "UTF-8 without BOM; newline=LF",
    "text_conversion": "wikitext_to_text, mwparserfromhell 0.7.2; then core clean_extracted and lexical_tokens",
}

_DROPPED_TAGS = {"ref", "references", "table", "gallery", "math", "chem", "score", "timeline", "syntaxhighlight"}
_DROPPED_LINK_PREFIXES = ("ficheiro:", "arquivo:", "imagem:", "file:", "image:", "categoria:", "category:")

Fetch = Callable[[dict], dict]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _api_get(params: dict) -> dict:
    query = {"action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content", "rvslots": "main",
             "format": "json", "formatversion": "2", **params}
    request = urllib.request.Request(f"{API}?{urllib.parse.urlencode(query)}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def _revision(payload: dict) -> dict:
    page = payload["query"]["pages"][0]
    if page.get("missing") or "revisions" not in page:
        raise LookupError(f"revisão não encontrada: {page.get('title')}")
    revision = page["revisions"][0]
    return {
        "title": page["title"],
        "pageid": page["pageid"],
        "revid": revision["revid"],
        "rev_timestamp": revision["timestamp"],
        "wikitext": revision["slots"]["main"]["content"],
    }


def fetch_latest(title: str, fetch: Fetch = _api_get) -> dict:
    return _revision(fetch({"titles": title, "redirects": "1"}))


def fetch_revision(revid: int, fetch: Fetch = _api_get) -> dict:
    return _revision(fetch({"revids": str(revid)}))


def wikitext_to_text(wikitext: str) -> str:
    code = mwparserfromhell.parse(wikitext)
    for tag in code.filter_tags(recursive=True):
        if str(tag.tag).strip().lower() in _DROPPED_TAGS:
            try:
                code.remove(tag)
            except ValueError:
                pass
    for link in code.filter_wikilinks(recursive=True):
        if str(link.title).strip().lower().startswith(_DROPPED_LINK_PREFIXES):
            try:
                code.remove(link)
            except ValueError:
                pass
    return code.strip_code(normalize=True, collapse=True)


def _entry(revision: dict, title_requested: str) -> dict:
    return {
        "title_requested": title_requested,
        "title": revision["title"],
        "pageid": revision["pageid"],
        "revid": revision["revid"],
        "rev_timestamp": revision["rev_timestamp"],
        "file": f"raw/{revision['pageid']}.wiki",
        "url": f"https://pt.wikipedia.org/w/index.php?oldid={revision['revid']}",
        "history_url": f"https://pt.wikipedia.org/w/index.php?curid={revision['pageid']}&action=history",
        "license": LICENSE,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": sha256_text(revision["wikitext"]),
    }


def _write_raw(out_dir: Path, entry: dict, wikitext: str) -> None:
    path = out_dir / entry["file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wikitext, encoding="utf-8", newline="\n")


def download_corpus(titles: list[str], out_dir: Path, fetch: Fetch = _api_get, pause_s: float = 1.0) -> dict:
    entries = []
    for title in titles:
        revision = fetch_latest(title, fetch)
        entry = _entry(revision, title)
        _write_raw(out_dir, entry, revision["wikitext"])
        entries.append(entry)
        time.sleep(pause_s)
    manifest = {"source": "pt.wikipedia.org", "license": LICENSE, "attribution": ATTRIBUTION,
                "extraction": EXTRACTION, "documents": entries}
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def restore_corpus(out_dir: Path, fetch: Fetch = _api_get, pause_s: float = 1.0, limit: int | None = None) -> int:
    """Baixa de novo cada revisão pelo oldid do manifesto e só grava se o hash conferir."""
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    restored = 0
    for entry in manifest["documents"][:limit]:
        revision = fetch_revision(entry["revid"], fetch)
        if revision["revid"] != entry["revid"] or revision["pageid"] != entry["pageid"]:
            raise ValueError(f"identidade da revisão não confere: oldid {entry['revid']}")
        if sha256_text(revision["wikitext"]) != entry["sha256"]:
            raise ValueError(f"hash não confere para oldid {entry['revid']} ({entry['title']})")
        _write_raw(out_dir, entry, revision["wikitext"])
        restored += 1
        time.sleep(pause_s)
    return restored


def manifest_hash(manifest: dict) -> str:
    stable = [{k: d[k] for k in ("pageid", "revid", "sha256")} for d in manifest["documents"]]
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()


def build_idf(corpus_dir: Path, tokenize: Callable[[str], list[str]]) -> dict:
    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    documents = []
    for entry in manifest["documents"]:
        wikitext = (corpus_dir / entry["file"]).read_text(encoding="utf-8")
        if sha256_text(wikitext) != entry["sha256"]:
            raise ValueError(f"hash não confere: {entry['file']}")
        documents.append(tokenize(wikitext_to_text(wikitext)))
    n_docs, df = document_frequencies(documents)
    return {"version": manifest_hash(manifest), "n_docs": n_docs, "df": dict(sorted(df.items()))}


def save_idf(table: dict, path: Path) -> None:
    path.write_text(json.dumps(table, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


def load_idf(path: Path) -> ReferenceIdf:
    table = json.loads(path.read_text(encoding="utf-8"))
    return ReferenceIdf(n_docs=table["n_docs"], df=table["df"], version=table["version"])
