from dataclasses import dataclass
import math

import numpy as np

from hts_core.domain import metrics


@dataclass(frozen=True)
class ModelInput:
    source_text: str
    suspect_text: str

    def __post_init__(self):
        if any(type(x) is not str or not x.strip() for x in (self.source_text, self.suspect_text)):
            raise ValueError('entrada do modelo exige dois textos não vazios')


def require_split(split):
    if split not in ('train', 'validation'):
        raise PermissionError('S5A não abre test para execução experimental; usar somente train/validation')


def validate_outputs(values, expected_count, task, labels=()):
    if type(expected_count) is not int or expected_count < 1 or len(values) != expected_count:
        raise ValueError('dimensão da saída difere das entradas')
    if task == 'H2':
        if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in values):
            raise ValueError('saída semântica exige escalar finito em [0,1]')
    elif task == 'H1':
        if not labels or any(v not in labels for v in values):
            raise ValueError('saída de classe fora do contrato')
    else:
        raise ValueError('tarefa de predição desconhecida')
    return values


def classification_report(truth, predictions, labels):
    counts = metrics.per_class_counts(truth, predictions, labels)
    return {'confusion': metrics.confusion_matrix(truth, predictions, labels), 'labels': list(labels),
            'n': len(truth), 'accuracy': metrics.multiclass_accuracy(truth, predictions),
            'macro_f1': metrics.macro_f1(truth, predictions, labels),
            'per_class': {label: {'precision': metrics.precision(c), 'recall': metrics.recall(c),
                                  'f1': metrics.f1(c), 'support': c.tp + c.fn}
                          for label, c in counts.items()},
            'zero_division': 0, 'absent_classes': 'included_in_macro', 'rounding': 'none'}


def regression_report(truth, predictions):
    result = {'n': len(truth), 'mae': metrics.mae(truth, predictions), 'mse': metrics.mse(truth, predictions)}
    for name in ('pearson', 'spearman', 'r2'):
        try:
            result[name] = {'status': 'defined', 'value': getattr(metrics, name)(truth, predictions)}
        except ValueError as exc:
            result[name] = {'status': 'undefined', 'value': None, 'reason': str(exc)}
    return result


def percentile(values, q):
    if not values or type(q) not in (int, float) or not math.isfinite(q) or not 0 <= q <= 1:
        raise ValueError('percentil exige valores e quantil entre zero e um')
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError('valores não finitos')
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    low, high = math.floor(index), math.ceil(index)
    return ordered[low] + (index - low) * (ordered[high] - ordered[low])


def latency_report(attempts):
    if not attempts or any(set(a) != {'status', 'seconds'} for a in attempts):
        raise ValueError('tentativas ausentes ou schema inválido')
    for row in attempts:
        if row['status'] not in ('ok', 'error', 'timeout') or type(row['seconds']) not in (int, float) or not math.isfinite(row['seconds']) or row['seconds'] < 0:
            raise ValueError('tentativa inválida')
    successful = [a['seconds'] for a in attempts if a['status'] == 'ok']
    return {'attempts': len(attempts), 'successes': len(successful),
            'failure_rate': 1 - len(successful) / len(attempts),
            'all_attempts_seconds': [a['seconds'] for a in attempts],
            'successful_seconds': {'p50': percentile(successful, .5), 'p95': percentile(successful, .95)} if successful else None,
            'quantile': 'linear_(n-1)*q', 'failed_attempts_retained': True}


def dependency_components(sources, pairs):
    group = {s['id']: s['group'] for s in sources}
    splits = {s['id']: s['split'] for s in sources}
    if len(group) != len(sources) or len({p['id'] for p in pairs}) != len(pairs):
        raise ValueError('IDs duplicados')
    for g in set(group.values()):
        if len({s['split'] for s in sources if s['group'] == g}) != 1:
            raise ValueError('família presente entre splits')
    parent = {g: g for g in group.values()}

    def find(g):
        while parent[g] != g:
            g = parent[g]
        return g

    for pair in pairs:
        refs = set(pair['source_ids']) | {pair['source_id']}
        refs.update(a['source_id'] for row in pair['sentences'] for a in row['ancestors'])
        if not refs <= group.keys() or any(splits[s] != pair['split'] for s in refs):
            raise ValueError('fonte ausente ou ancestralidade entre splits')
        roots = sorted({find(group[s]) for s in refs})
        for node in roots[1:]:
            parent[node] = roots[0]
    return {p['id']: find(group[p['source_id']]) for p in pairs}


def cluster_bootstrap_difference(truth, first, second, groups, labels, seed, repetitions=1000):
    metrics.confusion_matrix(truth, first, labels)
    metrics.confusion_matrix(truth, second, labels)
    if len(groups) != len(truth) or any(type(g) is not str or not g for g in groups):
        raise ValueError('grupos incompatíveis')
    unique = sorted(set(groups))
    if len(unique) < 2 or type(seed) is not int or type(repetitions) is not int or repetitions < 2:
        raise ValueError('reamostragem exige dois componentes, seed inteira e repetições>=2')
    members = {g: [i for i, value in enumerate(groups) if value == g] for g in unique}
    rng, differences = np.random.Generator(np.random.PCG64(seed)), []
    for _ in range(repetitions):
        indices = [i for g in rng.choice(unique, size=len(unique), replace=True) for i in members[g]]
        y = [truth[i] for i in indices]
        differences.append(metrics.macro_f1(y, [first[i] for i in indices], labels)
                           - metrics.macro_f1(y, [second[i] for i in indices], labels))
    return {'components': len(unique), 'seed': seed, 'repetitions': repetitions,
            'difference': metrics.macro_f1(truth, first, labels) - metrics.macro_f1(truth, second, labels),
            'interval95': [percentile(differences, .025), percentile(differences, .975)],
            'method': 'paired_component_percentile', 'draws': differences}
