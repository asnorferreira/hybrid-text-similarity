from collections import Counter

from hts_core.domain.metrics import spearman


CLASSES = ('copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada')
ANCHORS = (0, .25, .5, .75, 1)
AXES = {
    'thematic_overlap': ('none', 'some', 'strong', 'uncertain'),
    'propositional_relation': ('compatible', 'contradiction', 'unrelated', 'uncertain'),
    'shared_content': ('none', 'partial', 'predominant', 'equivalent', 'uncertain'),
    'context': ('sufficient', 'insufficient'),
}


def fields(value, expected, name):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(name + ': campos exatos exigidos')


def nonempty(value, name):
    if type(value) is not str or not value.strip() or len(value) > 4000:
        raise ValueError(name + ': texto não vazio de até 4000 caracteres exigido')


def validate_judgment(judgment, task, item):
    required = {'status', 'target', 'reason', 'quote_a', 'quote_b'}
    if task == 'H2':
        required.add('axes')
    fields(judgment, required, task)
    status, target = judgment['status'], judgment['target']
    if type(status) is not str or status not in ('labeled', 'ambiguous', 'excluded'):
        raise ValueError(task + ': estado ausente ou inválido')
    nonempty(judgment['reason'], task + '.reason')
    for key, text_key in (('quote_a', 'text_a'), ('quote_b', 'text_b')):
        quote = judgment[key]
        if type(quote) is not str or (quote and quote not in item[text_key]):
            raise ValueError(task + ': trecho de evidência não existe no texto')
        if status == 'labeled' and not quote.strip():
            raise ValueError(task + ': decisão válida exige trechos dos dois textos')
    if status != 'labeled' and target is not None:
        raise ValueError(task + ': ambíguo/excluído exige alvo nulo')
    if status == 'labeled':
        if task == 'H1' and (type(target) is not str or target not in CLASSES):
            raise ValueError('H1: classe inválida')
        if task == 'H2' and (type(target) not in (int, float) or target not in ANCHORS):
            raise ValueError('H2: nota deve ser uma âncora discreta, sem booleanos')
    if task == 'H2':
        axes = judgment['axes']
        fields(axes, AXES, 'H2.axes')
        for key, allowed in AXES.items():
            if type(axes[key]) is not str or axes[key] not in allowed:
                raise ValueError('H2: eixo inválido: ' + key)
        if status == 'labeled' and axes['context'] == 'insufficient':
            raise ValueError('H2: contexto insuficiente exige ambiguidade/exclusão')
        if status == 'labeled' and target == 1 and (
            axes['propositional_relation'] != 'compatible' or axes['shared_content'] != 'equivalent'
        ):
            raise ValueError('H2: nota 1 exige equivalência sem contradição')
        if axes['shared_content'] == 'equivalent' and axes['propositional_relation'] in ('contradiction', 'unrelated'):
            raise ValueError('H2: eixos contraditórios')


def agreement_and_consensus(first, second):
    left = {row['observation_id']: row for row in first['records']}
    right = {row['observation_id']: row for row in second['records']}
    if set(left) != set(right) or len(left) != len(first['records']) or len(right) != len(second['records']):
        raise ValueError('concordância exige os mesmos IDs únicos')
    if first['assessor_id'] == second['assessor_id']:
        raise ValueError('dois códigos de participantes distintos exigidos')
    common = {task: [(left[key][task]['target'], right[key][task]['target']) for key in sorted(left)
                    if left[key][task]['status'] == right[key][task]['status'] == 'labeled']
              for task in ('H1', 'H2')}
    nominal = common['H1']
    n = len(nominal)
    kappa: dict = {'value': None, 'n': n, 'reason': None}
    if not n:
        kappa['reason'] = 'nenhum par H1 válido nos dois participantes'
    else:
        counts_a, counts_b = Counter(a for a, _ in nominal), Counter(b for _, b in nominal)
        observed = sum(a == b for a, b in nominal) / n
        expected = sum(counts_a[c] * counts_b[c] for c in CLASSES) / (n * n)
        kappa.update(observed_agreement=observed, expected_agreement=expected,
                     marginal_counts=[dict(counts_a), dict(counts_b)])
        if expected == 1:
            kappa['reason'] = 'concordância esperada igual a 1; κ indefinido'
        else:
            kappa['value'] = (observed - expected) / (1 - expected)
    semantic = common['H2']
    correlation: dict = {'value': None, 'n': len(semantic), 'reason': None,
                                   'tie_policy': 'average_ranks'}
    try:
        correlation['value'] = spearman([a for a, _ in semantic], [b for _, b in semantic])
    except ValueError as exc:
        correlation['reason'] = str(exc)
    consensus = []
    for key in sorted(left):
        h1_a, h1_b = left[key]['H1'], right[key]['H1']
        h2_a, h2_b = left[key]['H2'], right[key]['H2']
        h1_valid = h1_a['status'] == h1_b['status'] == 'labeled' and h1_a['target'] == h1_b['target']
        h2_valid = h2_a['status'] == h2_b['status'] == 'labeled'
        consensus.append({'observation_id': key,
            'H1': {'target': h1_a['target'] if h1_valid else None,
                   'reason': None if h1_valid else 'sem duas decisões válidas e concordantes'},
            'H2': {'target': (h2_a['target'] + h2_b['target']) / 2 if h2_valid else None,
                   'reason': None if h2_valid else 'sem duas notas válidas'},
        })
    return {'H1_kappa': kappa, 'H2_spearman': correlation,
            'selected': len(left), 'H1_jointly_labeled': n, 'H2_jointly_labeled': len(semantic),
            'H1_missing_or_not_labeled': len(left) - n,
            'H2_missing_or_not_labeled': len(left) - len(semantic),
            'H1_disagreements': sum(a != b for a, b in nominal),
            'H2_distinct_scores': [len({a for a, _ in semantic}), len({b for _, b in semantic})],
            'H2_tied_observations': [
                sum(count for count in Counter(a for a, _ in semantic).values() if count > 1),
                sum(count for count in Counter(b for _, b in semantic).values() if count > 1),
            ],
            'consensus': consensus, 'individual_judgments_preserved': True,
            'population_inference_claimed': False, 'reference_frozen': False}
