"""Compara produção com constantes conferidas no PDF e recálculos independentes."""

import argparse
import json
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

import numpy as np

from tests.domain import test_reference_values as ref
from hts_core.domain.lexical import a1_tfidf_vectors, cosine, idf_a1
from hts_core.domain.metrics import accuracy, f1, pair_count, precision, recall, weighted_mean
from hts_core.domain.strings import common_prefix, jaro, jaro_winkler
from hts_core.domain.vectors import alignment_similarity
from hts_core.domain.signature import term_difference, term_difference_by_term_count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []

    def add(test, article, page, source, inputs, expected, obtained, tolerance, independent, kind):
        errors = [abs(a - b) for a, b in zip(obtained, expected)] if isinstance(expected, (tuple, list)) else [abs(obtained - expected)]
        row = dict(test=test, article=article, page=page, source=source, inputs=inputs,
                   expected=expected, obtained=obtained, tolerance=tolerance, independent=independent,
                   kind=kind, passed=all(e <= tolerance for e in errors))
        rows.append(row)

    with localcontext() as ctx:
        ctx.prec = 50
        for n, df, expected, tol, page in [(4, 1, .60206, 5e-6, "9/210"), (4, 2, .30103, 5e-6, "9/210"),
                                          (2, 2, 0., 0., "7/208"), (2, 1, .301029996, 5e-10, "7/208")]:
            independent = str((Decimal(n) / Decimal(df)).log10())
            test = {(4, 1): "test_a1_idf_df1_n4", (4, 2): "test_a1_idf_df2_n4",
                    (2, 2): "test_a1_idf_bisa_n2_df2_is_zero", (2, 1): "test_a1_table4_idf_aku_kenapa"}[n, df]
            add(test, "A1", page, "Tabs. 4/6, Eq. 1", f"N={n}, df={df}", expected,
                idf_a1(n, df), tol, independent, "valor publicado")
        vectors = a1_tfidf_vectors(ref.a1_documents())
        for term, (present, expected) in ref.A1_TABLE6.items():
            for document in present.split():
                add("test_a1_table7_every_weight_matches", "A1", "9–10/210–211", "Tabs. 6–7",
                    f"{term}, {document}, tf=1, df={len(present.split())}, N=4", expected,
                    vectors[document][term], 5e-6,
                    str((Decimal(4) / Decimal(len(present.split()))).log10()), "valor publicado")
        for other in ("d1", "d2", "d3"):
            oracle = str(1 / Decimal(750).sqrt()) if other == "d2" else "0"
            add("test_a1_table7_cosine_u_*", "A1", "9–10/210–211", "Tabs. 6–8; Eq. 3",
                f"tokens das Tabs. 6–7, u × {other}; d2: dot=b²; normas=5b, sqrt(30)b, b=log10(2)",
                .0365 if other == "d2" else 0., cosine(vectors["u"], vectors[other]),
                5e-5 if other == "d2" else 0., oracle, "recálculo; Tab. 8 publica 4% para d2")
        example = a1_tfidf_vectors({"u": ["bisa", "kenapa"], "d1": ["aku", "bisa"]})
        add("test_a1_tables4_5_cosine_u_d1_is_zero", "A1", "7/208", "Tabs. 4–5; Eq. 2",
            "u=[bisa,kenapa]; d1=[aku,bisa]; único termo comum tem IDF zero", 0.,
            cosine(example["u"], example["d1"]), 0., "0", "valor publicado e recálculo")
    add("test_a5_pair_count_n100", "A5", "6/315", "seção 3.1", "n=100", 4950, pair_count(100), 0,
        str(100 * 99 // 2), "valor publicado e recálculo")
    cases = [(117, 318, 37, 518, (.620, .933, .745, .641)),
             (11443, 6863, 3715, 14716, (.682, .798, .736, .712)),
             (300, 160, 240, 300, (.652, .556, .600, .600))]
    for figure, (tn, fp, fn, tp, expected) in zip(("9a", "9b", "10"), cases):
        c = ref.BinaryCounts(tn=tn, fp=fp, fn=fn, tp=tp)
        independent = [str(v) for v in (Fraction(tp, tp + fp), Fraction(tp, tp + fn),
                                       Fraction(2 * tp, 2 * tp + fp + fn), Fraction(tp + tn, tp + tn + fp + fn))]
        add(f"test_a5_confusion_matrices[Fig{figure}]", "A5", "13/322", f"Fig. {figure}",
            f"TN={tn}, FP={fp}, FN={fn}, TP={tp}; ordem=P,R,F1,Acc", expected,
            (precision(c), recall(c), f1(c), accuracy(c)), 5e-4, independent, "recálculo das matrizes publicadas")
    for table, data, weights, page, tol in [(1, ref.A8_TABLE1, ref.A8_TABLE1_PAIRS, "4/677", 5e-6),
                                           (2, ref.A8_TABLE2, ref.A8_TABLE2_PAIRS, "5/678", 5e-5)]:
        for run, (values, expected) in data.items():
            independent = sum(Fraction(str(v)) * w for v, w in zip(values, weights)) / sum(weights)
            add(f"test_a8_table{table}_weighted_mean[{run}]", "A8", page, f"Tab. {table}",
                f"valores={values}; pesos={weights}", expected, weighted_mean(values, weights), tol,
                str(independent), "média publicada; recálculo sobre valores arredondados")
    for tracks, expected, label in [(ref.A9_TABLE1_OFFICIAL, .6590, "oficial"),
                                    (ref.A9_TABLE1_CORRECTED, .6687, "corrigido")]:
        independent = sum(Fraction(str(v)) for v in tracks) / len(tracks)
        add(f"test_a9_table1_primary_is_simple_mean_of_tracks[{label}]", "A9", "4/188", "Tab. 1",
            str(tracks), expected, weighted_mean(tracks, [1] * len(tracks)), 5e-5,
            str(independent), "média publicada e recálculo")
    v = np.random.default_rng(0).normal(size=256)
    add("test_a9_identical_word_alignment_similarity_is_two", "A9", "2/186 e 6/190", "§3.4; Apêndice A",
        "vetor não nulo idêntico; teste: numpy default_rng(0), dimensão 256", 2.,
        alignment_similarity(v, v.copy()), 5e-3, "1 + (v·v)/(||v||²) = 2",
        "2,00 publicado para palavras iguais; vetor de teste é decisão do projeto")
    add("test_a6_table2_weighted_accuracy", "A6", "8–9/351–352", "§4.4; Tab. 2",
        "valores=[95,88,93]%; pesos=[70,80,50]", 91.7, weighted_mean([95, 88, 93], [70, 80, 50]),
        .05, str(Fraction(95 * 70 + 88 * 80 + 93 * 50, 200)),
        "recálculo ilustrativo; 91,7 não publicado, não prova a acurácia geral publicada de 92%")
    j, jw = jaro(ref.A4_TEXT1, ref.A4_TEXT2), jaro_winkler(ref.A4_TEXT1, ref.A4_TEXT2)
    rows.append(dict(test="test_a4_jaro_winkler_equals_jaro_without_common_prefix", article="A4",
                     page="3/153 e 5/155", source="Eq. 4; Fig. 1",
                     inputs=f"títulos: {ref.A4_TEXT1!r} × {ref.A4_TEXT2!r}; l=0",
                     expected="JW = J (identidade algébrica, sem escore esperado)",
                     obtained={"jaro": j, "jaro_winkler": jw}, tolerance=0.,
                     independent="l=0 => sim_JW=sim_J + 0*p*(1-sim_J)=sim_J",
                     kind="propriedade; escores dos títulos não reproduzem os 80,09% da Fig. 2",
                     passed=common_prefix(ref.A4_TEXT1, ref.A4_TEXT2) == 0 and j == jw))
    a, b = {"a", "b", "c", "d"}, {"a", "b", "e"}
    add("test_a3_denominator_uses_terms_of_document_smaller_by_size", "A3", "3/247 e 6/250", "§5.2 e §9",
        "EXEMPLO DO PROJETO: T1={a,b,c,d}, T2={a,b,e}; tamanhos=100,200; direção da prosa",
        .25, term_difference(a, b, 100, 200, direction="doc2_minus_doc1"), 0., "|{e}|/|T1| = 1/4",
        "recálculo independente complementar; listas do exemplo não foram publicadas no A3")
    add("test_a3_denominator_uses_terms_of_document_smaller_by_size", "A3", "3/247 e 6/250", "§5.2 e §9",
        "MESMO EXEMPLO DO PROJETO; direção do SQL", .5,
        term_difference(a, b, 100, 200, direction="doc1_minus_doc2"), 0., "|{c,d}|/|T1| = 2/4",
        "recálculo independente complementar; direção do artigo contraditória")
    add("test_a3_denominator_uses_terms_of_document_smaller_by_size", "A3", "3/247 e 6/250", "adaptação separada",
        "MESMO EXEMPLO DO PROJETO; adaptação por contagem de termos", 1 / 3,
        term_difference_by_term_count(a, b), 1e-15, "|{e}|/min(4,3) = 1/3",
        "adaptação do projeto; não é denominador da seção 9 do A3")
    for row in rows:
        row["evidence"] = (f"TCC/evidencias/codex-s0-s1/{row['article']}-texto.txt e {row['article']}-p*.png; "
                           "referencias.json na pasta de saída; logs de teste associados ao relatório da execução")
    args.out.joinpath("referencias.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    columns = ["test", "article", "page", "source", "inputs", "expected", "obtained", "tolerance", "independent", "kind", "evidence"]
    table = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    table += ["| " + " | ".join(str(row[c]).replace("|", "\\|").replace("\n", " ") for c in columns) + " |" for row in rows]
    args.out.joinpath("referencias.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "all_passed": all(r["passed"] for r in rows),
                      "source": "PDFs locais, imagens conferidas em 2026-10-24; entradas constantes em test_reference_values.py"}, ensure_ascii=False))
    if not all(r["passed"] for r in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
