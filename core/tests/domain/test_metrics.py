import pytest

from hts_core.domain.metrics import (
    BinaryCounts, confusion_matrix, f1, mae, macro_f1, mse, multiclass_accuracy, per_class_counts, precision, r2,
    weighted_mean, pearson, spearman,
)

LABELS = ["exata", "editada", "parafrase", "original"]
Y_TRUE = ["exata", "exata", "editada", "parafrase", "original", "original"]
Y_PRED = ["exata", "editada", "editada", "original", "original", "parafrase"]


def test_confusion_matrix_rows_are_true_labels():
    assert confusion_matrix(Y_TRUE, Y_PRED, LABELS) == [
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 1],
    ]


def test_per_class_counts_add_up_and_macro_f1():
    counts = per_class_counts(Y_TRUE, Y_PRED, LABELS)
    assert counts["exata"] == BinaryCounts(tp=1, fp=0, tn=4, fn=1)
    assert counts["editada"] == BinaryCounts(tp=1, fp=1, tn=4, fn=0)
    assert all(c.tp + c.fp + c.tn + c.fn == len(Y_TRUE) for c in counts.values())
    expected = (2 / 3 + 2 / 3 + 0 + 0.5) / 4
    assert macro_f1(Y_TRUE, Y_PRED, LABELS) == pytest.approx(expected)
    assert multiclass_accuracy(Y_TRUE, Y_PRED) == pytest.approx(3 / 6)


def test_zero_division_returns_zero():
    empty = BinaryCounts(tp=0, fp=0, tn=5, fn=0)
    assert precision(empty) == 0.0 and f1(empty) == 0.0


def test_regression_metrics_known_case():
    y, y_hat = [1.0, 2.0, 3.0, 4.0], [1.5, 2.0, 2.5, 4.0]
    assert mse(y, y_hat) == pytest.approx(0.125)
    assert mae(y, y_hat) == pytest.approx(0.25)
    assert r2(y, y_hat) == pytest.approx(1 - 0.5 / 5.0)


def test_weighted_mean_rejects_bad_input():
    with pytest.raises(ValueError):
        weighted_mean([1.0], [0])
    with pytest.raises(ValueError):
        weighted_mean([1.0, 2.0], [1])


def test_error_means_accept_single_pair_but_reject_empty_input():
    assert mse([1.0], [3.0]) == 4.0
    assert mae([1.0], [3.0]) == 2.0
    for function in (mse, mae):
        with pytest.raises(ValueError):
            function([], [])


def test_correlations_and_r2_reject_undefined_cases():
    for function in (pearson, spearman):
        with pytest.raises(ValueError):
            function([1.0], [2.0])
        with pytest.raises(ValueError, match="variância zero"):
            function([1.0, 1.0], [2.0, 3.0])
    with pytest.raises(ValueError, match="variância zero"):
        r2([1.0, 1.0], [2.0, 3.0])
