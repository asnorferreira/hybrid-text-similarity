import warnings

import numpy as np

from hts_core.adapters.dataset_store import identity
from hts_core.domain.experiments import classification_report


def predict_export(export, features):
    if export.get('schema') != 'hts-scalar-logistic-1' or export.get('identity') != identity({k:v for k,v in export.items() if k != 'identity'}):
        raise ValueError('invalid classifier export identity')
    x = np.asarray(features, dtype=float)
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
    if set(train_features) != systems or set(validation_features) != systems:
        raise ValueError('all three comparable systems required')
    if set(train_targets) != set(spec['classes']):
        raise ValueError('all adopted classes required')
    result = {}
    params = spec['classifier']
    for system in sorted(systems):
        x = np.asarray(train_features[system],dtype=float)
        v = np.asarray(validation_features[system],dtype=float)
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
                  'preprocessing':'one scalar unchanged; no standardization; no metadata features',
                  'sklearn_version':sklearn.__version__,'bindings':bindings}
        export['identity']=identity(export)
        predictions=predict_export(export,v.tolist())
        if predictions != model.predict(v[:,None]).tolist():
            raise RuntimeError('portable classifier differs from fitted model')
        result[system]={'model':export,'validation':classification_report(validation_targets,predictions,spec['classes']),
                        'predictions':predictions,'failures':0}
    return result
