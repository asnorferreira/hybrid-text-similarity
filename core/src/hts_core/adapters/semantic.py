import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import threading

MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
REVISION = 'e8f8c211226b894fcb81acc59f3b34ba3efd5f42'
DEFAULT_CACHE = Path(__file__).resolve().parents[3] / 'models' / REVISION
FILES = ['1_Pooling/config.json', 'README.md', 'config.json', 'config_sentence_transformers.json',
         'model.safetensors', 'modules.json', 'sentence_bert_config.json', 'sentencepiece.bpe.model',
         'special_tokens_map.json', 'tokenizer.json', 'tokenizer_config.json', 'unigram.json']


class ResourceUnavailable(RuntimeError):
    pass


def cache_path():
    return Path(os.environ.get('HTS_MODEL_PATH', DEFAULT_CACHE))


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def prepare_cache(path=None):
    from huggingface_hub import HfApi, snapshot_download
    target = Path(path) if path else cache_path()
    info = HfApi().model_info(MODEL, revision=REVISION)
    if info.sha != REVISION or info.card_data is None or info.card_data.license != 'apache-2.0':
        raise ResourceUnavailable('revisão/licença do modelo diverge do contrato')
    snapshot_download(MODEL, revision=REVISION, local_dir=target, allow_patterns=FILES)
    hashes = {name: digest(target / name) for name in FILES}
    descriptor = {'model': MODEL, 'revision': REVISION, 'license': 'apache-2.0', 'files': hashes}
    descriptor['identity'] = hashlib.sha256(json.dumps(descriptor, sort_keys=True).encode()).hexdigest()
    (target / 'hts-model.json').write_text(json.dumps(descriptor, indent=2), encoding='utf-8')
    return descriptor


class SemanticEncoder:
    def __init__(self, path=None):
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.base.modules.transformer import Transformer
        import torch
        torch.set_num_threads(int(os.environ.get('HTS_TORCH_THREADS', '2')))
        target = Path(path) if path else cache_path()
        try:
            descriptor = json.loads((target / 'hts-model.json').read_text(encoding='utf-8'))
            if descriptor['revision'] != REVISION or descriptor['model'] != MODEL:
                raise ValueError('identidade divergente')
            for name in FILES:
                if digest(target / name) != descriptor['files'][name]:
                    raise ValueError('hash divergente')
            self.model = SentenceTransformer(str(target), device='cpu', local_files_only=True, trust_remote_code=False)
        except (OSError, ValueError, KeyError, ImportError, RuntimeError) as exc:
            raise ResourceUnavailable('cache semântico ausente, inválido ou incompatível') from exc
        self.model.eval()
        self.tokenizer = self.model.tokenizer
        transformer = self.model[0]
        if not isinstance(transformer, Transformer):
            raise ResourceUnavailable('pinned encoder has no Transformer module')
        self.limit = min(self.model.max_seq_length, transformer.auto_model.config.max_position_embeddings,
                         self.tokenizer.model_max_length)
        self.special = self.tokenizer.num_special_tokens_to_add(pair=False)
        self.capacity = self.limit - self.special
        self.lock = threading.Lock()
        self.identity = {**{k: descriptor[k] for k in ('model', 'revision', 'license', 'identity')},
                         'dimension': self.model.get_embedding_dimension(), 'limit': self.limit,
                         'special_tokens': self.special, 'content_capacity': self.capacity,
                         'runtime': {name: importlib.metadata.version(name) for name in
                                     ('sentence-transformers', 'transformers', 'torch', 'tokenizers')}}

    def tokens(self, text):
        return self.tokenizer(text, add_special_tokens=False, truncation=False)['input_ids']

    def encode(self, texts, max_tokens=12000):
        import numpy as np
        import torch
        from hts_core.domain.hybrid import pool_windows

        outputs, diagnostics = [], []
        with self.lock, torch.inference_mode():
            repeated = {}
            deterministic = not any(module.training for module in self.model.modules())
            for text in texts:
                if deterministic and text in repeated:
                    index = repeated[text]
                    outputs.append(outputs[index])
                    diagnostics.append({**diagnostics[index], 'window_tokens': list(diagnostics[index]['window_tokens'])})
                    continue
                encoded = self.tokenizer(text, add_special_tokens=False, truncation=False).encodings[0]
                ids = encoded.ids
                if len(ids) > max_tokens:
                    raise ValueError('limite de tokens de conteúdo excedido')
                encoded.truncate(self.capacity, stride=0)
                chunks = [encoded, *encoded.overflowing]
                embeddings = []
                for chunk in chunks:
                    prepared = self.tokenizer.backend_tokenizer.post_process(chunk, add_special_tokens=True)
                    features = {name: torch.tensor([values]) for name, values in
                                [('input_ids', prepared.ids), ('attention_mask', prepared.attention_mask),
                                 ('token_type_ids', prepared.type_ids)]}
                    if features['input_ids'].shape[1] > self.limit:
                        raise ValueError('janela excede capacidade efetiva')
                    embedding = self.model(features)['sentence_embedding'][0].cpu().numpy()
                    embeddings.append(embedding)
                if [token for chunk in chunks for token in chunk.ids] != ids:
                    raise ValueError('cobertura de tokens divergente')
                outputs.append(pool_windows(embeddings, [len(chunk.ids) for chunk in chunks]))
                diagnostics.append({'content_tokens': len(ids), 'windows': len(chunks),
                                    'window_tokens': [len(chunk.ids) for chunk in chunks], 'covered_tokens': sum(len(chunk.ids) for chunk in chunks)})
                if deterministic and len(repeated) < 128:
                    repeated[text] = len(outputs) - 1
        return np.asarray(outputs), diagnostics
