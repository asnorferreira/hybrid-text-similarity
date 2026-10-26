import hashlib
import importlib.metadata
import importlib.util
import json
import platform
from pathlib import Path
import unicodedata

from hts_core.adapters import nlp
from hts_core.adapters.refcorpus import load_idf, manifest_hash
from hts_core.adapters.semantic import ResourceUnavailable

CORE = Path(__file__).resolve().parents[3]


def load_policy():
    path = CORE / 'configs/comparison.json'
    data = path.read_bytes()
    config = json.loads(data)
    if config['semantic_weight'] != .6 or config['lexical_weight'] != .4 or config['policy'] != 'q5-v2':
        raise ValueError('política de fusão incompatível')
    config['file_sha256'] = hashlib.sha256(data).hexdigest()
    sources = ['domain/hybrid.py', 'domain/lexical.py', 'domain/text.py', 'domain/preprocess.py', 'domain/strings.py',
               'domain/signature.py', 'application/text_pipeline.py', 'application/comparison.py', 'adapters/semantic.py',
               'adapters/nlp.py', 'adapters/resources.py', 'adapters/schemas.py', 'adapters/http.py']
    config['implementation_sha256'] = {name: hashlib.sha256((CORE/'src/hts_core'/name).read_bytes()).hexdigest() for name in sources}
    return config, hashlib.sha256(json.dumps(config, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def idf_resource(path=None):
    path = Path(path) if path else CORE / 'data/refcorpus/idf.json'
    try:
        table = load_idf(path)
        manifest = json.loads((CORE/'data/refcorpus/manifest.json').read_text(encoding='utf-8'))
        if table.version != manifest_hash(manifest) or table.n_docs != len(manifest['documents']):
            raise ValueError('corpus/tabela incompatíveis')
        for entry in manifest['documents']:
            if hashlib.sha256((CORE/'data/refcorpus'/entry['file']).read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('hash raw divergente')
        if table.n_docs < 1 or not table.version or any(not isinstance(df, int) or not 0 <= df <= table.n_docs for df in table.df.values()):
            raise ValueError('tabela inválida')
        files = {str(p.relative_to(CORE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                 [CORE/'src/hts_core/domain/text.py', CORE/'src/hts_core/domain/preprocess.py',
                  CORE/'src/hts_core/domain/lexical.py', CORE/'src/hts_core/adapters/nlp.py',
                  CORE/'src/hts_core/adapters/refcorpus.py', CORE/'data/refcorpus/manifest.json']}
        descriptor = {'historical_version': table.version, 'table_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                      'observed_pipeline': files, 'spacy_model': nlp.model_info(),
                      'runtime': {name: importlib.metadata.version(name) for name in ('spacy', 'numpy', 'mwparserfromhell')},
                      'construction_attestation': False, 'formula': 'tf_count * (ln((1+N)/(1+df))+1); unknown df=0'}
        model_spec = importlib.util.find_spec(nlp.SPACY_MODEL)
        if model_spec is None or model_spec.origin is None:
            raise ImportError('spaCy model module has no filesystem origin')
        model_root = Path(model_spec.origin).parent
        descriptor['spacy_assets_sha256'] = {p.relative_to(model_root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                           for p in sorted(model_root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        descriptor['lexical_configuration'] = {'stopwords': sorted(nlp.STOPWORDS), 'disabled': ['parser', 'ner'],
                                               'min_token_length': 3, 'tf': 'raw_count', 'vector_normalization': 'cosine_only',
                                               'corpus_config_sha256': hashlib.sha256((CORE/'configs/refcorpus_provisorio.yaml').read_bytes()).hexdigest()}
        descriptor['python'] = platform.python_version()
        descriptor['unicode'] = unicodedata.unidata_version
        descriptor['identity'] = hashlib.sha256(json.dumps(descriptor, sort_keys=True).encode()).hexdigest()
        return table, descriptor
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        raise ResourceUnavailable('IDF ou pipeline lexical indisponível') from exc
