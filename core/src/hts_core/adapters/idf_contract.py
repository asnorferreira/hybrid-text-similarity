from datetime import datetime
from pathlib import Path

from hts_core.adapters.contract_types import number, object_fields, sha256, string_list, text
from hts_core.adapters.dataset_store import digest, identity, inside, read_json, read_jsonl, verify_seal

LEXICAL_CODE = ('application/dataset_pipeline.py', 'application/text_pipeline.py', 'adapters/nlp.py',
                'domain/lexical.py', 'domain/preprocess.py', 'domain/text.py')
IDF_SETTINGS = {'formula': 'ln((1+N)/(1+df))+1', 'tf': 'raw_count', 'unknown_df': 0,
                'vector_normalization': 'cosine_only'}


def validate_pipeline(pipeline):
    object_fields(pipeline, {'code', 'disabled', 'font_assets', 'generator_scripts', 'lock_sha256', 'model',
                            'model_assets', 'packages', 'python', 'stopwords', 'text_hash_policy', 'unicode'}, 'idf.pipeline')
    for field in ('python', 'unicode', 'text_hash_policy'):
        text(pipeline[field], 'pipeline.'+field)
    sha256(pipeline['lock_sha256'], 'pipeline.lock_sha256')
    object_fields(pipeline['model'], {'name', 'version', 'license'}, 'pipeline.model')
    for value in pipeline['model'].values():
        text(value, 'pipeline.model')
    for field in ('code', 'model_assets', 'font_assets', 'generator_scripts', 'packages'):
        mapping = pipeline[field]
        if type(mapping) is not dict or not mapping:
            raise ValueError('pipeline.'+field+': inventário não vazio exigido')
        for key, value in mapping.items():
            text(key, 'pipeline.'+field+'.key')
            (text if field == 'packages' else sha256)(value, 'pipeline.'+field+'.value')
    if not set(LEXICAL_CODE) <= pipeline['code'].keys():
        raise ValueError('pipeline: código produtor lexical ausente')
    if pipeline['disabled'] != ['parser', 'ner']:
        raise ValueError('pipeline.disabled divergente')
    string_list(pipeline['stopwords'], 'pipeline.stopwords', empty=True)


def lexical_projection(pipeline):
    validate_pipeline(pipeline)
    return {**{key: pipeline[key] for key in ('model', 'model_assets', 'stopwords', 'disabled', 'python',
                                              'unicode', 'text_hash_policy', 'lock_sha256')},
            'code': {key: pipeline['code'][key] for key in LEXICAL_CODE},
            'packages': {key: pipeline['packages'][key] for key in ('spacy', 'pt-core-news-sm', 'numpy')}}


def validate_training_idf_contract(folder, idf_folder, expected_identity=None):
    folder, idf_folder = Path(folder), Path(idf_folder)
    manifest = verify_seal(folder)
    config, pipeline = read_json(folder/'config.json'), read_json(folder/'pipeline.json')
    sources = [s for s in read_jsonl(folder/'sources.jsonl') if s['split'] == 'train']
    table, descriptor, execution = [read_json(idf_folder/name) for name in ('idf.json', 'construction.json', 'execution.json')]
    object_fields(table, {'n_docs', 'df', 'formula', 'tf', 'unknown_df', 'vector_normalization', 'version'}, 'idf.table')
    object_fields(descriptor, {'purpose', 'construction_attestation', 'allowed_split', 'training_sources', 'pipeline',
                               'table_content_sha256', 'config', 'input_identity', 'identity'}, 'idf.construction')
    object_fields(execution, {'dataset_version', 'constructed_utc', 'platform', 'serialized_table_sha256'}, 'idf.execution')
    number(table['n_docs'], 'idf.n_docs', integer=True, positive=True)
    if table['n_docs'] != len(sources):
        raise ValueError('idf.n_docs: N difere das fontes reais de treino')
    if type(table['df']) is not dict:
        raise ValueError('idf.df: objeto exigido')
    for term, count in table['df'].items():
        text(term, 'idf.df.term')
        number(count, 'idf.df.count', integer=True, positive=True)
        if count > table['n_docs']:
            raise ValueError('idf.df: df excede N')
    for field, expected in IDF_SETTINGS.items():
        if type(table[field]) is not type(expected) or table[field] != expected:
            raise ValueError('idf.'+field+': contrato incompatível')
    expected_purpose = {'frozen_operational_derivation': 'operational_derivation',
                        'frozen_derivation_candidate': 'experimental_candidate'}.get(manifest['metadata']['purpose'], manifest['metadata']['purpose'])
    if type(config) is not dict or config.get('purpose') != expected_purpose:
        raise ValueError('idf: finalidade config/manifesto divergente')
    if type(descriptor['config']) is not dict or identity(descriptor['config']) != identity(config):
        raise ValueError('idf.config: configuração de construção divergente')
    if descriptor['purpose'] != config['purpose'] or descriptor['allowed_split'] != 'train' or descriptor['construction_attestation'] is not True:
        raise ValueError('idf: finalidade/allowed_split/atestado incompatível')
    expected_sources = []
    if len({s['id'] for s in sources}) != len(sources):
        raise ValueError('idf: fontes duplicadas')
    for source in sources:
        text(source['id'], 'source.id')
        text(source['text'], 'source.text')
        number(source['revision'], 'source.revision', integer=True, positive=True)
        for field, file_field in (('raw_sha256', 'raw_file'), ('normalized_sha256', 'normalized_file')):
            sha256(source[field], 'source.'+field)
            text(source[file_field], 'source.'+file_field)
            if digest(inside(folder, source[file_field]).read_bytes()) != source[field]:
                raise ValueError('idf: bytes da fonte divergem de '+field)
        expected_sources.append({key: source[key] for key in ('id', 'revision', 'raw_sha256', 'normalized_sha256')})
    if type(descriptor['training_sources']) is not list or descriptor['training_sources'] != expected_sources:
        raise ValueError('idf.training_sources: dados de teste/validação ou origem/revisão/hash/ordem divergentes do treino')
    for source in descriptor['training_sources']:
        object_fields(source, {'id', 'revision', 'raw_sha256', 'normalized_sha256'}, 'idf.training_source')
        text(source['id'], 'idf.training_source.id')
        number(source['revision'], 'idf.training_source.revision', integer=True, positive=True)
        sha256(source['raw_sha256'], 'idf.training_source.raw_sha256')
        sha256(source['normalized_sha256'], 'idf.training_source.normalized_sha256')
    if descriptor['input_identity'] != identity([{'id': s['id'], 'text': s['text']} for s in sources]):
        raise ValueError('idf.input_identity: conteúdo de entrada divergente')
    validate_pipeline(descriptor['pipeline'])
    if descriptor['pipeline'] != pipeline:
        raise ValueError('idf.pipeline: produtor diverge do pipeline selado com as entradas')
    for value, path in ((table['version'], 'idf.version'), (descriptor['identity'], 'idf.identity'),
                        (descriptor['table_content_sha256'], 'idf.table_content_sha256'),
                        (execution['dataset_version'], 'execution.dataset_version'),
                        (execution['serialized_table_sha256'], 'execution.serialized_table_sha256')):
        sha256(value, path)
    if descriptor['table_content_sha256'] != identity({k: v for k, v in table.items() if k != 'version'}):
        raise ValueError('idf: conteúdo da tabela adulterado')
    if descriptor['identity'] != identity({k: v for k, v in descriptor.items() if k != 'identity'}) or table['version'] != descriptor['identity']:
        raise ValueError('idf: identidade de construção divergente')
    if expected_identity is not None and table['version'] != expected_identity:
        raise ValueError('idf: versão difere do protocolo')
    allowed = {manifest['version']}
    if manifest['metadata']['purpose'] == 'frozen_operational_derivation' and 'parent_version' in manifest['metadata']:
        parent = manifest['metadata']['parent_version']
        sha256(parent, 'manifest.parent_version')
        review = read_json(folder/'review.json')
        proof = read_json(folder/'freeze-authorization.json')['reproduction']
        payload = {k: v for k, v in manifest['files'].items() if k not in {'review.json', 'freeze-authorization.json'}}
        if config.get('record_contract') == 'assessment_v2':
            payload['pairs.jsonl'] = payload.pop('construction-pairs.jsonl')
        if (review.get('dataset_version') != parent or proof.get('original_version') != parent
                or proof.get('reconstructed_version') != parent or proof.get('file_inventory_sha256') != identity(payload)):
            raise ValueError('idf: pai de congelamento diverge da revisão/reprodução/inventário preservados')
        allowed.add(parent)
    if execution['dataset_version'] not in allowed:
        raise ValueError('idf.execution: versão não é a candidata/congelada permitida')
    if execution['serialized_table_sha256'] != digest((idf_folder/'idf.json').read_bytes()):
        raise ValueError('idf.execution: bytes serializados divergentes')
    text(execution['platform'], 'execution.platform')
    timestamp = datetime.fromisoformat(text(execution['constructed_utc'], 'execution.constructed_utc'))
    if timestamp.utcoffset() is None:
        raise ValueError('idf.execution: timestamp exige fuso')
    return {'version': table['version'], 'n_docs': table['n_docs'], 'terms': len(table['df']),
            'integrity': 'verified', 'contract_and_input_binding': 'verified',
            'producer_binding': 'verified_against_sealed_dataset_pipeline',
            'current_runtime_producer_equivalence': 'not_checked', 'lexical_recomputation': 'not_executed',
            'prior_lexical_recomputation_reused_as_current': False,
            'lexical_verification_path': 'python -m hts_core.cli dataset validar-idf --dataset DATASET --idf IDF (explicit full lexical recomputation)',
            'scope': 'A_integrity_and_B_contract_inputs_complete; C_lexical_df_not_recomputed'}
