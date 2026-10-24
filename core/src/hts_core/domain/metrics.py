import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BinaryCounts:
    tp: int
    fp: int
    tn: int
    fn: int

    def __post_init__(self) -> None:
        if any(not isinstance(n, int) or n < 0 for n in (self.tp, self.fp, self.tn, self.fn)):
            raise ValueError("contagens devem ser inteiros não negativos")


def _ratio(num: float, den: float) -> float:
    return num / den if den else 0.0


def precision(c: BinaryCounts) -> float:
    return _ratio(c.tp, c.tp + c.fp)


def recall(c: BinaryCounts) -> float:
    return _ratio(c.tp, c.tp + c.fn)


def f1(c: BinaryCounts) -> float:
    p, r = precision(c), recall(c)
    return _ratio(2 * p * r, p + r)


def accuracy(c: BinaryCounts) -> float:
    return _ratio(c.tp + c.tn, c.tp + c.fp + c.tn + c.fn)


def pair_count(n: int) -> int:
    """A5, nº de pares."""
    return math.comb(n, 2)


def weighted_mean(values: Sequence[float], weights: Sequence[float]) -> float:
    if len(values) != len(weights) or not values:
        raise ValueError("valores e pesos precisam ter o mesmo tamanho, não nulo")
    total = sum(weights)
    if total == 0:
        raise ValueError("soma dos pesos é zero")
    return sum(v * w for v, w in zip(values, weights)) / total


def confusion_matrix(y_true: Sequence[Hashable], y_pred: Sequence[Hashable],
                     labels: Sequence[Hashable]) -> list[list[int]]:
    if not labels or len(set(labels)) != len(labels):
        raise ValueError("rótulos devem ser únicos e não vazios")
    index = {label: i for i, label in enumerate(labels)}
    matrix = [[0] * len(labels) for _ in labels]
    for t, p in zip(y_true, y_pred, strict=True):
        matrix[index[t]][index[p]] += 1
    return matrix


def per_class_counts(y_true: Sequence[Hashable], y_pred: Sequence[Hashable],
                     labels: Sequence[Hashable]) -> dict[Hashable, BinaryCounts]:
    matrix = confusion_matrix(y_true, y_pred, labels)
    total = len(y_true)
    counts = {}
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fn = sum(matrix[i]) - tp
        fp = sum(row[i] for row in matrix) - tp
        counts[label] = BinaryCounts(tp=tp, fp=fp, tn=total - tp - fn - fp, fn=fn)
    return counts


def macro_f1(y_true: Sequence[Hashable], y_pred: Sequence[Hashable], labels: Sequence[Hashable]) -> float:
    counts = per_class_counts(y_true, y_pred, labels)
    return sum(f1(c) for c in counts.values()) / len(labels)


def multiclass_accuracy(y_true: Sequence[Hashable], y_pred: Sequence[Hashable]) -> float:
    if len(y_true) != len(y_pred) or not y_true:
        raise ValueError("sequências vazias ou de tamanhos diferentes")
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)


def _check_pair(x: Sequence[float], y: Sequence[float], minimum: int = 1) -> None:
    if len(x) != len(y) or len(x) < minimum:
        raise ValueError(f"são necessários ao menos {minimum} pares de mesmo tamanho")


def mse(y: Sequence[float], y_hat: Sequence[float]) -> float:
    _check_pair(y, y_hat)
    return sum((a - b) ** 2 for a, b in zip(y, y_hat)) / len(y)


def mae(y: Sequence[float], y_hat: Sequence[float]) -> float:
    _check_pair(y, y_hat)
    return sum(abs(a - b) for a, b in zip(y, y_hat)) / len(y)


def r2(y: Sequence[float], y_hat: Sequence[float]) -> float:
    _check_pair(y, y_hat)
    mean = sum(y) / len(y)
    ss_tot = sum((a - mean) ** 2 for a in y)
    if ss_tot == 0:
        raise ValueError("variância zero em y")
    ss_res = sum((a - b) ** 2 for a, b in zip(y, y_hat))
    return 1 - ss_res / ss_tot


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    _check_pair(x, y, minimum=2)
    mx, my = sum(x) / len(x), sum(y) / len(y)
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        raise ValueError("variância zero")
    return cov / (sx * sy)


def average_ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = rank
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))
