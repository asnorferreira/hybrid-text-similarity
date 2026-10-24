import math

import numpy as np

COSINE_TOLERANCE = 1e-12
LABELS = ('copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada')


def bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    value = float(value)
    if not math.isfinite(value) or value < low - COSINE_TOLERANCE or value > high + COSINE_TOLERANCE:
        raise ValueError('escore não finito ou fora do domínio')
    return min(high, max(low, value))


def unit_vector(vector) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float64)
    if vector.ndim != 1 or not vector.size or not np.isfinite(vector).all():
        raise ValueError('vetor inválido')
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError('norma nula ou não finita')
    return vector / norm


def semantic_cosine(a, b) -> float:
    a, b = unit_vector(a), unit_vector(b)
    if a.shape != b.shape:
        raise ValueError('dimensões incompatíveis')
    return bounded(np.dot(a, b), -1, 1)


def operational_cosine(value: float) -> float:
    return max(0.0, bounded(value, -1, 1))


def pool_windows(vectors, token_counts) -> np.ndarray:
    if not len(vectors) or len(vectors) != len(token_counts):
        raise ValueError('janelas e pesos incompatíveis')
    weights = np.asarray(token_counts, dtype=np.float64)
    if not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError('pesos de tokens devem ser positivos')
    normalized = np.asarray([unit_vector(v) for v in vectors])
    return unit_vector(np.average(normalized, axis=0, weights=weights))


def content_windows(ids: list[int], capacity: int) -> list[list[int]]:
    if not ids or capacity < 1:
        raise ValueError('conteúdo ou capacidade vazios')
    return [ids[start:start + capacity] for start in range(0, len(ids), capacity)]


def score_matrix(matrix) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2 or not all(matrix.shape):
        raise ValueError('matriz deve ser não vazia e bidimensional')
    return np.asarray([[bounded(x) for x in row] for row in matrix])


def fuse(lexical, semantic):
    lexical = score_matrix(lexical)
    semantic = np.asarray(semantic, dtype=np.float64)
    if lexical.shape != semantic.shape:
        raise ValueError('matrizes incompatíveis')
    operational = np.asarray([[operational_cosine(x) for x in row] for row in semantic])
    return operational, 0.6 * operational + 0.4 * lexical


def similarity_index(matrix, source_weights, suspect_weights) -> dict:
    matrix = score_matrix(matrix)
    weights = [np.asarray(w, dtype=np.float64) for w in (source_weights, suspect_weights)]
    for axis, w in enumerate(weights):
        if w.ndim != 1 or len(w) != matrix.shape[axis] or not np.isfinite(w).all() or (w < 0).any() or not w.sum():
            raise ValueError('documento sem peso útil ou pesos inválidos')
    forward = float(np.average(matrix.max(axis=1), weights=weights[0]))
    reverse = float(np.average(matrix.max(axis=0), weights=weights[1]))
    return {'source_to_suspect': forward, 'suspect_to_source': reverse, 'value': 50 * (forward + reverse)}


def hungarian(matrix) -> dict:
    matrix = score_matrix(matrix)
    rows, cols = matrix.shape
    n = max(rows, cols)
    costs = np.zeros((n, n))
    costs[:rows, :cols] = -matrix
    u, v = [0.] * (n + 1), [0.] * (n + 1)
    p, way = [0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minimum, used = [math.inf] * (n + 1), [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], math.inf, 0
            for j in range(1, n + 1):
                if not used[j]:
                    current = costs[i0 - 1, j - 1] - u[i0] - v[j]
                    if current < minimum[j]:
                        minimum[j], way[j] = current, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    pairs = sorted((p[j] - 1, j - 1) for j in range(1, n + 1)
                   if p[j] <= rows and j <= cols and matrix[p[j] - 1, j - 1] > 0)
    return {'pairs': [{'source': i, 'suspect': j, 'score': float(matrix[i, j])} for i, j in pairs],
            'unmatched_source': [i for i in range(rows) if i not in {a for a, _ in pairs}],
            'unmatched_suspect': [j for j in range(cols) if j not in {b for _, b in pairs}],
            'objective': sum(float(matrix[i, j]) for i, j in pairs)}


def classify_pair(source: str, suspect: str, lexical: float, semantic: float, edit: float,
                  edited_threshold=.8, low_threshold=.3, paraphrase_threshold=.75, lexical_high=.85) -> dict:
    if not source or not suspect:
        raise ValueError('par vazio não é classificado')
    lexical, semantic, edit = map(bounded, (lexical, semantic, edit))
    for t in (edited_threshold, low_threshold, paraphrase_threshold, lexical_high):
        bounded(t)
    if source == suspect:
        label, reason = LABELS[0], 'igualdade_da_representacao_textual'
    elif edit >= edited_threshold:
        label, reason = LABELS[1], 'semelhanca_estrutural'
    elif max(lexical, semantic) <= low_threshold:
        label, reason = LABELS[3], 'escores_baixos_sem_evidencia_estrutural'
    elif semantic > paraphrase_threshold:
        label, reason = LABELS[2], 'similaridade_semantica_operacional'
    else:
        label, reason = LABELS[3], 'evidencia_insuficiente_pelas_regras'
    return {'label': label, 'reason': reason, 'lexical_high': lexical > lexical_high}


def class_summary(labels: list[str]) -> dict:
    if not labels or any(label not in LABELS for label in labels):
        raise ValueError('classes ausentes ou inválidas')
    counts = {label: labels.count(label) for label in LABELS}
    winners = [label for label, count in counts.items() if count == max(counts.values())]
    return {'counts': counts, 'proportions': {label: count / len(labels) for label, count in counts.items()},
            'denominator': len(labels), 'predominance': winners[0] if len(winners) == 1 else 'sem_predominancia',
            'inserted_segment': 'indisponivel_regra_nao_definida'}
