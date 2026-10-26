import math
from pathlib import Path
import warnings

import numpy as np

from hts_core.adapters.contract_types import object_fields, string_list, text
from hts_core.adapters.dataset_store import identity, read_json
from hts_core.domain.experiments import classification_report

PREPROCESSING = 'contracted features unchanged; no standardization; no metadata features'


def profile():
    from hts_core.adapters.training_contract import validate_s5b
    value = read_json(Path(__file__).resolve().parents[3] / 'configs/experiment_s5b.r3.json')
    validate_s5b(value)
    return value['h1']


def feature_array(system, values):
    spec = profile()['features_by_system']
    if system not in spec or type(values) is not list:
        raise ValueError('unknown system or invalid feature rows')
    width = len(spec[system])
    rows = [[v] for v in values] if width == 1 else values
    if any(type(r) is not list or len(r) != width for r in rows):
        raise ValueError('feature dimensions differ from contract')
    low = -1 if system == 'semantic' else 0
    if any(type(v) not in (int, float) or not math.isfinite(v) or not low <= v <= 1 for r in rows for v in r):
        raise ValueError('invalid or forbidden feature value')
    return np.asarray(rows, dtype=float).reshape(len(rows), width)


def validate_export(value, expected_bindings=None):
    object_fields(value, {'schema','system','classes','coefficients','intercepts','configuration','feature',
                         'preprocessing','sklearn_version','bindings','identity'}, 'classifier')
    if value['schema'] != 'hts-logistic-2' or value['identity'] != identity({k:v for k,v in value.items() if k != 'identity'}):
        raise ValueError('invalid classifier export identity')
    spec = profile()
    if value['system'] not in spec['features_by_system']:
        raise ValueError('unknown classifier system')
    string_list(value['classes'], 'classifier.classes', set(spec['classes']))
    if len(value['classes']) != 4 or value['feature'] != spec['features_by_system'][value['system']]:
        raise ValueError('classifier classes/features differ from adopted contract')
    expected = spec['classifier']
    object_fields(value['configuration'], set(expected), 'classifier.configuration')
    for key, v in expected.items():
        actual = value['configuration'][key]
        valid = type(actual) in (int,float) and math.isfinite(actual) if type(v) is float else type(actual) is type(v)
        if not valid or actual != v:
            raise ValueError('classifier configuration differs: '+key)
    if value['preprocessing'] != PREPROCESSING:
        raise ValueError('classifier preprocessing differs')
    text(value['sklearn_version'], 'classifier.sklearn_version')
    if type(value['bindings']) is not dict or not value['bindings']:
        raise ValueError('classifier bindings required')
    if expected_bindings is not None and identity(value['bindings']) != identity(expected_bindings):
        raise ValueError('classifier bindings differ')
    width = len(value['feature'])
    if (type(value['coefficients']) is not list or len(value['coefficients']) != 4 or
        any(type(r) is not list or len(r) != width for r in value['coefficients']) or
        type(value['intercepts']) is not list or len(value['intercepts']) != 4):
        raise ValueError('classifier dimensions differ')
    if any(type(v) not in (int,float) or not math.isfinite(v) for r in value['coefficients']+[value['intercepts']] for v in r):
        raise ValueError('nonfinite classifier parameters')
    return value


def predict_export(value, features, *, expected_bindings=None):
    validate_export(value, expected_bindings)
    x = feature_array(value['system'], features)
    scores = x @ np.asarray(value['coefficients']).T + np.asarray(value['intercepts'])
    return [value['classes'][i] for i in scores.argmax(axis=1)]


def fit_classifiers(train_features, validation_features, train_targets, validation_targets, spec, bindings):
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    import sklearn
    if identity(spec) != identity(profile()):
        raise ValueError('classifier specification differs from adopted revision')
    systems = set(spec['features_by_system'])
    if set(train_features) != systems or set(validation_features) != systems:
        raise ValueError('all four comparable systems required')
    if set(train_targets) != set(spec['classes']) or any(train_targets.count(c) < 2 for c in spec['classes']):
        raise ValueError('at least two training examples of every class required')
    result = {}
    params = spec['classifier']
    for system in sorted(systems):
        x = feature_array(system, train_features[system])
        v = feature_array(system, validation_features[system])
        if len(x) != len(train_targets) or len(v) != len(validation_targets):
            raise ValueError('common comparison incomplete')
        model = LogisticRegression(C=params['C'], max_iter=params['max_iter'], random_state=params['seed'], solver='lbfgs')
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            model.fit(x, train_targets)
        export = dict(schema='hts-logistic-2', system=system, classes=model.classes_.tolist(),
                      coefficients=np.asarray(model.coef_).tolist(), intercepts=np.asarray(model.intercept_).tolist(),
                      configuration=params, feature=spec['features_by_system'][system], preprocessing=PREPROCESSING,
                      sklearn_version=sklearn.__version__, bindings=bindings)
        export['identity'] = identity(export)
        predictions = predict_export(export, validation_features[system], expected_bindings=bindings)
        if predictions != np.asarray(model.predict(v)).tolist():
            raise RuntimeError('portable classifier differs from fitted model')
        training_predictions = predict_export(export, train_features[system], expected_bindings=bindings)
        result[system] = dict(model=export, fit_iterations=np.asarray(model.n_iter_).tolist(), predictions=predictions, failures=0,
            training=classification_report(train_targets, training_predictions, spec['classes']),
            validation=classification_report(validation_targets, predictions, spec['classes']))
    return result
