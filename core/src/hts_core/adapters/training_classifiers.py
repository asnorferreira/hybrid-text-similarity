import warnings
import math
from pathlib import Path

import numpy as np

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.adapters.contract_types import object_fields, string_list, text
from hts_core.domain.experiments import classification_report


PREPROCESSING = 'one scalar unchanged; no standardization; no metadata features'


def _profile():
    from hts_core.adapters.training_contract import validate_s5b
    config = read_json(Path(__file__).resolve().parents[3]/'configs/experiment_s5b.json')
    validate_s5b(config)
    return config['h1']


def validate_export(export, expected_bindings=None):
    object_fields(export, {'schema','system','classes','coefficients','intercepts','configuration','feature',
                          'preprocessing','sklearn_version','bindings','identity'}, 'classifier')
    if export['schema'] != 'hts-scalar-logistic-1' or export['identity'] != identity({k:v for k,v in export.items() if k != 'identity'}):
        raise ValueError('invalid classifier export identity')
    spec = _profile()
    text(export['system'], 'classifier.system')
    if export['system'] not in spec['features_by_system']:
        raise ValueError('unknown classifier system')
    string_list(export['classes'], 'classifier.classes', set(spec['classes']))
    if len(export['classes']) != 4 or export['feature'] != spec['features_by_system'][export['system']]:
        raise ValueError('classifier classes/feature differ from adopted contract')
    expected = spec['classifier']
    object_fields(export['configuration'], set(expected), 'classifier.configuration')
    for key, value in expected.items():
        actual = export['configuration'][key]
        valid = (type(actual) in (int,float) and math.isfinite(actual)) if type(value) is float else type(actual) is type(value)
        if not valid or actual != value:
            raise ValueError('classifier configuration differs: '+key)
    if export['preprocessing'] != PREPROCESSING:
        raise ValueError('classifier preprocessing differs')
    text(export['sklearn_version'], 'classifier.sklearn_version')
    if type(export['bindings']) is not dict or not export['bindings']:
        raise ValueError('classifier bindings required')
    if expected_bindings is not None and identity(export['bindings']) != identity(expected_bindings):
        raise ValueError('classifier bindings differ from expected inputs')
    if (type(export['coefficients']) is not list or len(export['coefficients']) != 4 or
            any(type(row) is not list or len(row) != 1 for row in export['coefficients']) or
            type(export['intercepts']) is not list or len(export['intercepts']) != 4):
        raise ValueError('classifier dimensions differ from contract')
    values = [row[0] for row in export['coefficients']]+export['intercepts']
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError('classifier parameters require finite numbers without booleans')
    return export


def _feature_array(system, features):
    low = -1 if system == 'semantic' else 0
    if type(features) is not list or any(type(v) not in (int,float) or not math.isfinite(v) or not low <= v <= 1 for v in features):
        raise ValueError('features require finite numeric scalars within contracted cosine/fusion range')
    return np.asarray(features,dtype=float)


def predict_export(export, features, *, expected_bindings=None):
    validate_export(export, expected_bindings)
    x = _feature_array(export['system'],features)
    coef = np.asarray(export['coefficients'], dtype=float)
    intercept = np.asarray(export['intercepts'], dtype=float)
    if x.ndim != 1 or coef.shape != (4,1) or intercept.shape != (4,) or len(set(export['classes'])) != 4:
        raise ValueError('classifier dimensions/classes differ from contract')
    if not all(np.isfinite(v).all() for v in (x,coef,intercept)):
        raise ValueError('nonfinite classifier data')
    scores = x[:,None]*coef[:,0]+intercept
    return [export['classes'][i] for i in scores.argmax(axis=1)]


def fit_classifiers(train_features, validation_features, train_targets, validation_targets, spec, bindings):
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    import sklearn
    systems = {'lexical','semantic','fixed_fusion'}
    if identity(spec) != identity(_profile()):
        raise ValueError('classifier specification differs from adopted profile')
    if set(train_features) != systems or set(validation_features) != systems:
        raise ValueError('all three comparable systems required')
    if set(train_targets) != set(spec['classes']):
        raise ValueError('all adopted classes required')
    result = {}
    params = spec['classifier']
    for system in sorted(systems):
        x = _feature_array(system,train_features[system])
        v = _feature_array(system,validation_features[system])
        if x.shape != (len(train_targets),) or v.shape != (len(validation_targets),) or not np.isfinite(x).all() or not np.isfinite(v).all():
            raise ValueError('missing/nonfinite system features; common comparison incomplete')
        model = LogisticRegression(C=params['C'], max_iter=params['max_iter'], random_state=params['seed'],
                                   class_weight=None, solver='lbfgs')
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning)
            model.fit(x[:,None],train_targets)
        export = {'schema':'hts-scalar-logistic-1','system':system,'classes':model.classes_.tolist(),
                  'coefficients':model.coef_.tolist(),'intercepts':model.intercept_.tolist(),
                  'configuration':params,'feature':spec['features_by_system'][system],
                  'preprocessing':PREPROCESSING,
                  'sklearn_version':sklearn.__version__,'bindings':bindings}
        export['identity']=identity(export)
        predictions=predict_export(export,v.tolist(),expected_bindings=bindings)
        if predictions != model.predict(v[:,None]).tolist():
            raise RuntimeError('portable classifier differs from fitted model')
        training_predictions = predict_export(export,x.tolist(),expected_bindings=bindings)
        result[system]={'model':export,'fit_iterations':model.n_iter_.tolist(),
                        'training':classification_report(train_targets,training_predictions,spec['classes']),
                        'validation':classification_report(validation_targets,predictions,spec['classes']),
                        'predictions':predictions,'failures':0}
    return result


def save_fitted_classifiers(results, destination, bindings):
    from hts_core.adapters.experiment_io import save_json_new
    from hts_core.adapters.dataset_store import digest
    if set(results) != {'lexical','semantic','fixed_fusion'}:
        raise ValueError('all three classifier artifacts required')
    artifacts = {}
    for system, result in results.items():
        export = validate_export(result['model'],bindings)
        if export['system'] != system:
            raise ValueError('classifier system differs from artifact name')
        relative = 'classifiers/'+system+'.json'
        path = Path(destination)/relative
        save_json_new(path,export)
        loaded = read_json(path)
        validate_export(loaded,bindings)
        if identity(loaded) != identity(export):
            raise ValueError('persisted classifier differs')
        artifacts[system] = {'path':relative,'sha256':digest(path.read_bytes()),'identity':loaded['identity'],'loaded':True}
    return artifacts
