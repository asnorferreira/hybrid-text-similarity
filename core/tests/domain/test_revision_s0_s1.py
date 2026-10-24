import pytest
from rapidfuzz.distance import DamerauLevenshtein, OSA

from hts_core.domain.metrics import BinaryCounts, confusion_matrix, macro_f1
from hts_core.domain.strings import damerau_levenshtein_distance
from hts_core.domain.text import clean_extracted, split_sentences


def test_successive_line_breaks_in_the_same_word_are_all_joined():
    assert clean_extracted("algo-\nrit-\nmo") == "algoritmo"
    assert clean_extracted("guarda-\nchuva e algo-\nrit-\nmo") == "guarda-chuva e algoritmo"


def test_decimal_at_sentence_end_does_not_hide_the_next_sentence():
    assert split_sentences("O valor é 3.5. Próxima frase.") == ["O valor é 3.5.", "Próxima frase."]


def test_osa_and_unrestricted_damerau_levenshtein_are_distinct_variants():
    assert damerau_levenshtein_distance("CA", "ABC") == 3
    assert OSA.distance("CA", "ABC") == 3
    assert DamerauLevenshtein.distance("CA", "ABC") == 2


@pytest.mark.parametrize("labels", [[], ["a", "a"]])
def test_class_metrics_reject_empty_or_duplicate_label_universe(labels):
    for function in (confusion_matrix, macro_f1):
        with pytest.raises(ValueError, match="rótulos"):
            function(["a"], ["a"], labels)


@pytest.mark.parametrize("counts", [(-1, 0, 0, 0), (1.5, 0, 0, 0)])
def test_binary_counts_are_nonnegative_integers(counts):
    with pytest.raises(ValueError, match="contagens"):
        BinaryCounts(*counts)
