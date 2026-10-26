from tests.domain import test_reference_values as ref

from hts_core.domain.lexical import a1_tfidf_vectors, cosine, idf_a1
from hts_core.domain.metrics import BinaryCounts, accuracy, f1, pair_count, precision, recall, weighted_mean
from hts_core.domain.strings import jaro, jaro_winkler

rows = []
v = a1_tfidf_vectors(ref.a1_documents())
rows += [
    ("A1 idf N=4 df=1", idf_a1(4, 1)),
    ("A1 idf N=4 df=2", idf_a1(4, 2)),
    ("A1 idf N=2 df=2 (bisa)", idf_a1(2, 2)),
    ("A1 idf N=2 df=1 (Tab. 4)", idf_a1(2, 1)),
    ("A1 cos(U,D1) Tab. 4-5", cosine(*a1_tfidf_vectors({"u": ["bisa", "kenapa"], "d1": ["aku", "bisa"]}).values())),
    ("A1 cos(u,d2) Tab. 7", cosine(v["u"], v["d2"])),
    ("A1 cos(u,d1) Tab. 7", cosine(v["u"], v["d1"])),
    ("A1 cos(u,d3) Tab. 7", cosine(v["u"], v["d3"])),
    ("A5 C(100,2)", pair_count(100)),
]
for name, c in [("A5 Fig. 9a", BinaryCounts(tn=117, fp=318, fn=37, tp=518)),
                ("A5 Fig. 9b", BinaryCounts(tn=11443, fp=6863, fn=3715, tp=14716)),
                ("A5 Fig. 10", BinaryCounts(tn=300, fp=160, fn=240, tp=300))]:
    rows.append((f"{name} P/R/F1/Acc", tuple(round(x, 6) for x in (precision(c), recall(c), f1(c), accuracy(c)))))
for run in sorted(ref.A8_TABLE1):
    rows.append((f"A8 Tab. 1 {run}", weighted_mean(ref.A8_TABLE1[run][0], ref.A8_TABLE1_PAIRS)))
for run in sorted(ref.A8_TABLE2):
    rows.append((f"A8 Tab. 2 {run}", weighted_mean(ref.A8_TABLE2[run][0], ref.A8_TABLE2_PAIRS)))
rows += [
    ("A9 Tab. 1 oficial", weighted_mean(ref.A9_TABLE1_OFFICIAL, [1] * 7)),
    ("A9 Tab. 1 corrigido", weighted_mean(ref.A9_TABLE1_CORRECTED, [1] * 7)),
    ("A6 Tab. 2 acurácia ponderada", weighted_mean([95, 88, 93], [70, 80, 50])),
    ("A4 Fig. 1 jaro", jaro(ref.A4_TEXT1, ref.A4_TEXT2)),
    ("A4 Fig. 1 jaro_winkler", jaro_winkler(ref.A4_TEXT1, ref.A4_TEXT2)),
]
for name, value in rows:
    print(f"{name}\t{value}")
