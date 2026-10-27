"""Opt-in demonstration of frozen models, separate from the Q5-V2 index."""
import hashlib
import json
import os
from pathlib import Path

from hts_core.adapters.resources import CORE
from hts_core.adapters.semantic import ResourceUnavailable


def load_config():
    path = Path(os.environ.get('HTS_TRAINED_MODELS_CONFIG', str(CORE / 'configs/trained_models.json')))
    try:
        value = json.loads(path.read_text())
        if (set(value) != {'schema', 'enabled', 'files', 'h1', 'idf', 'h2_protocol', 'h2_checkpoint', 'platt'} or
                value['schema'] != 'hts-trained-models-1' or type(value['enabled']) is not bool):
            raise ValueError('invalid trained model configuration')
        for key in ('h1', 'idf', 'h2_protocol', 'h2_checkpoint', 'platt'):
            if type(value[key]) is not str or Path(value[key]).is_absolute() or '..' in Path(value[key]).parts:
                raise ValueError('core-relative artifact paths required')
        if type(value['files']) is not dict or (value['enabled'] and not value['files']):
            raise ValueError('frozen artifact inventory required')
        value['config_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        return value
    except (OSError, ValueError, TypeError) as exc:
        raise ResourceUnavailable('configuração dos modelos treinados indisponível') from exc


class TrainedModels:
    def __init__(self, encoder, config):
        try:
            from hts_core.adapters.dataset_store import read_json
            from hts_core.adapters.trainable_siamese import Siamese, WindowEncoder
            from hts_core.adapters.training_artifacts import load_inference_weights
            from hts_core.adapters.training_classifiers_v2 import validate_export
            from hts_core.adapters.calibration_resources import load_p1_resources
            from hts_core.application.calibration import predict_platt
            from hts_core.domain.lexical import ReferenceIdf
            required = [config[k] for k in ('h1', 'idf', 'h2_protocol', 'platt')]
            required += [config['h2_checkpoint'] + '/' + name for name in ('manifest.json', 'weights.safetensors')]
            for name in required:
                path = (CORE / name).resolve()
                if (not path.is_relative_to(CORE) or name not in config['files'] or
                        hashlib.sha256(path.read_bytes()).hexdigest() != config['files'][name]):
                    raise ValueError('frozen artifact differs')
            self.h1 = read_json(CORE / config['h1'])
            validate_export(self.h1)
            if self.h1['system'] != 'learned_fusion':
                raise ValueError('learned fusion export required')
            table = read_json(CORE / config['idf'])
            self.idf = ReferenceIdf(table['n_docs'], table['df'], table['version'])
            self.platt = read_json(CORE / config['platt'])
            predict_platt(self.platt, [.5], self.platt['bindings'])
            # Verify P1's original application IDF, base encoder and numeric policy.
            load_p1_resources(encoder)
            spec = read_json(CORE / config['h2_protocol'])['siamese']
            self.siamese = Siamese(WindowEncoder(encoder.model, encoder.tokenizer, encoder.limit),
                spec['embedding_dimension'], spec['dense_dimensions'][1], spec['dropout'],
                spec['leaky_relu_alpha'], spec['layer_norm_epsilon'], spec['encoder_trainable'])
            checkpoint = CORE / config['h2_checkpoint']
            load_inference_weights(checkpoint, self.siamese, read_json(checkpoint/'manifest.json')['bindings'])
            self.siamese.eval()
            for p in self.siamese.parameters():
                p.requires_grad_(False)
            self.encoder = encoder
            self.identities = [
                {'name': 'Fusão aprendida H1', 'version': self.h1['schema'], 'sha256': config['files'][config['h1']]},
                {'name': 'Siamês H2', 'version': Path(config['h2_checkpoint']).name, 'sha256': config['files'][config['h2_checkpoint']+'/weights.safetensors']},
                {'name': 'Platt P1', 'version': self.platt['schema'], 'sha256': config['files'][config['platt']]},
            ]
            self.config_sha256 = config['config_sha256']
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            raise ResourceUnavailable('artefatos dos modelos treinados indisponíveis ou incompatíveis') from exc

    def enrich(self, result):
        import torch
        from hts_core.adapters.training_classifiers_v2 import predict_export
        from hts_core.application.calibration import predict_platt
        from hts_core.domain.lexical import cosine
        from hts_core.domain.hybrid import bounded
        # Preserve the trained H2 forward path: its window pooling differs from
        # Q5-V2's per-window normalization on multi-window sentences. The base
        # weights stay shared; WindowEncoder's frozen bounded cache is retained.
        # No targets, ancestry, IDs or transformation metadata are features.
        rows = []
        with self.encoder.lock, torch.no_grad():
            try:
                for match in result['matches']:
                    i, j = match['source'], match['suspect']
                    a, b = result['source'][i], result['suspect'][j]
                    lexical = bounded(cosine(self.idf.vector(a['lexical']), self.idf.vector(b['lexical'])))
                    semantic = match['semantic_raw']
                    label = predict_export(self.h1, [[lexical, max(0., semantic)]], expected_bindings=self.h1['bindings'])[0]
                    score = float(self.siamese(a['semantic'], b['semantic']))
                    probability = predict_platt(self.platt, [match['fused']], self.platt['bindings'])[0]
                    rows.append({'source': i, 'suspect': j, 'h1_label': label, 'h2_score': score,
                                 'derivation_probability': probability})
            finally:
                # Training diagnostics are per-run; serving must not grow an
                # unbounded list over the lifetime of the HTTP process.
                self.siamese.encoder.diagnostics.clear()
        result['trained_models'] = {'state': 'calculated', 'config_sha256': self.config_sha256,
            'models': self.identities, 'scope': 'best_q5v2_pairs_exploratory_not_document_index', 'pairs': rows}
        result['metadata']['unavailable_components'] = ['inserted_segment']
        return result
