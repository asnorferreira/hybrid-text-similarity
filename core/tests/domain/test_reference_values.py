import numpy as np
import pytest

from hts_core.domain.lexical import a1_tfidf_vectors, cosine, idf_a1
from hts_core.domain.metrics import BinaryCounts, accuracy, f1, pair_count, precision, recall, weighted_mean
from hts_core.domain.strings import common_prefix, jaro, jaro_winkler
from hts_core.domain.vectors import alignment_similarity

# A1, Tabela 6 (p. 210, PDF p. 9): token → (documentos em que aparece, idf impresso); Tab. 7 (pp. 210–211) repete esses pesos
A1_TABLE6 = {
    "era": ("u", 0.60206),
    "globalisasi": ("u", 0.60206),
    "ini": ("u", 0.60206),
    "kembang": ("u d2", 0.30103),
    "pola": ("u", 0.60206),
    "hidup": ("u", 0.60206),
    "masyarakat": ("u", 0.60206),
    "plagiarisme": ("d1", 0.60206),
    "tindak": ("d1", 0.60206),
    "langgar": ("d1", 0.60206),
    "momok": ("d1", 0.60206),
    "ilmu": ("d1 d2", 0.30103),
    "tahu": ("d1", 0.60206),
    "laku": ("d1", 0.60206),
    "lapor": ("d2", 0.60206),
    "teliti": ("d2", 0.60206),
    "fakultas": ("d2", 0.60206),
    "dana": ("d2", 0.60206),
    "boptn": ("d2", 0.60206),
    "tahun": ("d2", 0.60206),
    "anggar": ("d2", 0.60206),
    "aplikasi": ("d3", 0.60206),
    "terap": ("d3", 0.60206),
    "algoritma": ("d3", 0.60206),
    "cocok": ("d3", 0.60206),
    "string": ("d3", 0.60206),
    "dokumen": ("d3", 0.60206),
}


def a1_documents():
    docs = {"u": [], "d1": [], "d2": [], "d3": []}
    for token, (present, _) in A1_TABLE6.items():
        for name in present.split():
            docs[name].append(token)
    return docs


# A1, Tab. 6, p. 210
def test_a1_idf_df1_n4():
    assert idf_a1(4, 1) == pytest.approx(0.60206, abs=5e-6)


def test_a1_idf_df2_n4():
    assert idf_a1(4, 2) == pytest.approx(0.30103, abs=5e-6)


# A1, Tab. 4, p. 208
def test_a1_idf_bisa_n2_df2_is_zero():
    assert idf_a1(2, 2) == 0.0


# A1, Tab. 4, p. 208 (impresso 0.301029996)
def test_a1_table4_idf_aku_kenapa():
    assert idf_a1(2, 1) == pytest.approx(0.301029996, abs=5e-10)


def test_a1_tables4_5_cosine_u_d1_is_zero():
    vectors = a1_tfidf_vectors({"u": ["bisa", "kenapa"], "d1": ["aku", "bisa"]})
    assert vectors["u"]["bisa"] == 0.0 and vectors["d1"]["bisa"] == 0.0
    assert vectors["u"]["kenapa"] == pytest.approx(0.301029996, abs=5e-10)
    assert cosine(vectors["u"], vectors["d1"]) == 0.0


def test_a1_table7_every_weight_matches():
    vectors = a1_tfidf_vectors(a1_documents())
    for token, (present, printed_idf) in A1_TABLE6.items():
        for name in present.split():
            assert vectors[name][token] == pytest.approx(printed_idf, abs=5e-6), (token, name)


# mapa, "Valores de referência" (recálculo da Tab. 7; a Tab. 8, p. 211, imprime 4%)
def test_a1_table7_cosine_u_d2():
    vectors = a1_tfidf_vectors(a1_documents())
    assert cosine(vectors["u"], vectors["d2"]) == pytest.approx(0.0365, abs=5e-5)


@pytest.mark.parametrize("other", ["d1", "d3"])
def test_a1_table7_cosine_u_without_shared_terms_is_zero(other):
    vectors = a1_tfidf_vectors(a1_documents())
    assert cosine(vectors["u"], vectors[other]) == 0.0


# A5, p. 315 (100 documentos, 4950 entradas)
def test_a5_pair_count_n100():
    assert pair_count(100) == 4950


# A5, Figs. 9a, 9b e 10, p. 322 (matrizes); esperados do mapa, "Valores de referência"
@pytest.mark.parametrize(
    "counts, expected",
    [
        (BinaryCounts(tn=117, fp=318, fn=37, tp=518), (0.620, 0.933, 0.745, 0.641)),
        (BinaryCounts(tn=11443, fp=6863, fn=3715, tp=14716), (0.682, 0.798, 0.736, 0.712)),
        (BinaryCounts(tn=300, fp=160, fn=240, tp=300), (0.652, 0.556, 0.600, 0.600)),
    ],
    ids=["A5_fig9a_privado", "A5_fig9b_MIT", "A5_fig10_online"],
)
def test_a5_confusion_matrices(counts, expected):
    obtained = (precision(counts), recall(counts), f1(counts), accuracy(counts))
    assert obtained == pytest.approx(expected, abs=5e-4)


# A8, Tab. 1, p. 677 (pares, Pearson por conjunto e média ponderada impressa)
A8_TABLE1_PAIRS = [254, 249, 230, 244, 209]
A8_TABLE1 = {
    "run1": ([0.58873, 0.73458, 0.76887, 0.85020, 0.69306], 0.72646),
    "run2": ([0.57739, 0.75061, 0.80068, 0.82857, 0.73035], 0.73569),
    "run3": ([0.61426, 0.77263, 0.80500, 0.84840, 0.74705], 0.75607),
}
# A8, Tab. 2, p. 678
A8_TABLE2_PAIRS = [375, 750, 375, 750, 750]
A8_TABLE2 = {
    "run1": ([0.7049, 0.7422, 0.7287, 0.7630, 0.8198], 0.7604),
    "run2": ([0.6660, 0.6770, 0.7439, 0.7749, 0.8576], 0.7536),
    "run3": ([0.7246, 0.7416, 0.7389, 0.7776, 0.8367], 0.7719),
}


@pytest.mark.parametrize("run", sorted(A8_TABLE1))
def test_a8_table1_weighted_mean(run):
    values, expected = A8_TABLE1[run]
    assert weighted_mean(values, A8_TABLE1_PAIRS) == pytest.approx(expected, abs=5e-6)


@pytest.mark.parametrize("run", sorted(A8_TABLE2))
def test_a8_table2_weighted_mean(run):
    values, expected = A8_TABLE2[run]
    assert weighted_mean(values, A8_TABLE2_PAIRS) == pytest.approx(expected, abs=5e-5)


# A9, Tab. 1, p. 188 (trilhas; Primary impresso 0.6590 e corrigido 0.6687)
A9_TABLE1_OFFICIAL = [0.7294, 0.6753, 0.8202, 0.7802, 0.1598, 0.8053, 0.6430]
A9_TABLE1_CORRECTED = [0.7294, 0.6753, 0.8202, 0.7802, 0.1598, 0.8329, 0.6831]


@pytest.mark.parametrize(
    "tracks, expected",
    [(A9_TABLE1_OFFICIAL, 0.6590), (A9_TABLE1_CORRECTED, 0.6687)],
    ids=["oficial", "corrigido"],
)
def test_a9_table1_primary_is_simple_mean_of_tracks(tracks, expected):
    assert weighted_mean(tracks, [1] * len(tracks)) == pytest.approx(expected, abs=5e-5)


# A9, seção 3.4, p. 186; Apêndice A, p. 190: palavra idêntica = 2,00
def test_a9_identical_word_alignment_similarity_is_two():
    v = np.random.default_rng(0).normal(size=256)
    assert alignment_similarity(v, v.copy()) == pytest.approx(2.00, abs=5e-3)


# A6, pp. 351–352: exercício aritmético, sem reconstruir a acurácia global.
def test_a6_table2_weighted_accuracy():
    assert weighted_mean([95, 88, 93], [70, 80, 50]) == pytest.approx(91.7, abs=0.05)


# A4, Fig. 1, p. 155 (PDF p. 5): títulos visíveis dos dois textos de exemplo, sem prefixo comum
A4_TEXT1 = "How AI is Transforming the Software Development Process"
A4_TEXT2 = "The Role of Artificial Intelligence in Modern Software Development"


def test_a4_jaro_winkler_equals_jaro_without_common_prefix():
    assert common_prefix(A4_TEXT1, A4_TEXT2) == 0
    assert jaro_winkler(A4_TEXT1, A4_TEXT2) == jaro(A4_TEXT1, A4_TEXT2)
    assert 0 < jaro(A4_TEXT1, A4_TEXT2) < 1
