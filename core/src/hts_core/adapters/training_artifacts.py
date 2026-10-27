from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.checkpoint_retention import safe_path


def load_inference_weights(checkpoint, model, expected_bindings):
    from hts_core.adapters.tensor_storage import load_weights_bounded
    from hts_core.adapters.training_runtime import file_hash
    if type(expected_bindings) is not dict or not expected_bindings:
        raise ValueError('expected execution bindings required')
    root = safe_path(checkpoint)
    manifest = read_json(safe_path(root/'manifest.json'))
    if (manifest.get('schema') != 'hts-training-checkpoint-1' or
            identity(manifest.get('bindings')) != identity(expected_bindings) or
            manifest.get('bindings_identity') != identity(expected_bindings)):
        raise ValueError('inference checkpoint bindings differ')
    if type(manifest.get('files')) is not dict or set(manifest['files']) != {'weights.safetensors','local-state.pt'}:
        raise ValueError('checkpoint components missing or unknown')
    for name, expected in manifest['files'].items():
        if file_hash(safe_path(root/name)) != expected:
            raise ValueError('inference checkpoint bytes altered: '+name)
    load_weights_bounded(root/'weights.safetensors', model)
    model.eval()
    return {'schema':'hts-inference-load-receipt-1','bindings_identity':identity(expected_bindings),
            'weights_sha256':manifest['files']['weights.safetensors'],
            'optimizer_and_rng_loaded':False,'origin_authentication':'not_implied_by_hash',
            'scope':'weights only; relocated checkpoint allowed; not optimizer resumption'}
