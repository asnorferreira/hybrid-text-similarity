from hts_core.domain.preprocess import lexical_tokens, remove_noise, semantic_text
from hts_core.domain.text import clean_extracted, split_sentences, word_count


def test_soft_hyphen_at_line_end_joins_word():
    assert clean_extracted("a infor­\nmação foi") == "a informação foi"


def test_soft_hyphen_inside_word_is_removed():
    assert clean_extracted("subs­tituição") == "substituição"


def test_hard_hyphen_line_break_with_lowercase_continuation_joins():
    assert clean_extracted("o algo-\n  ritmo compara") == "o algoritmo compara"


def test_hard_hyphen_line_break_with_uppercase_keeps_hyphen():
    assert clean_extracted("Rio-\nGrande") == "Rio-Grande"


def test_hyphen_inside_line_is_kept():
    assert clean_extracted("guarda-chuva e fazê-lo") == "guarda-chuva e fazê-lo"


def test_whitespace_ligatures_and_paragraphs():
    raw = "Primeira  linha\ncontinua\r\n\r\n\nﬁm do  texto\t"
    assert clean_extracted(raw) == "Primeira linha continua\n\nfim do texto"


def test_split_sentences_basic_and_question_exclamation():
    text = "O texto é curto. Ele tem perguntas? Sim! E termina aqui."
    assert split_sentences(text) == ["O texto é curto.", "Ele tem perguntas?", "Sim!", "E termina aqui."]


def test_split_sentences_keeps_abbreviations_initials_and_decimals():
    text = "O Dr. Silva e a Profa. Lima citam J. Souza et al. Na p. 12 o valor é 3.5 vezes maior. Fim."
    assert split_sentences(text) == [
        "O Dr. Silva e a Profa. Lima citam J. Souza et al. Na p. 12 o valor é 3.5 vezes maior.",
        "Fim.",
    ]


def test_split_sentences_quotes_and_paragraph_boundary():
    text = "Ele disse: \"Acabou.\" Depois saiu.\n\nnovo parágrafo sem maiúscula"
    assert split_sentences(text) == ["Ele disse: \"Acabou.\"", "Depois saiu.", "novo parágrafo sem maiúscula"]


def test_lowercase_after_period_is_not_a_boundary():
    assert split_sentences("Ver item a. depois o b.") == ["Ver item a. depois o b."]


def test_word_count():
    assert word_count("Três palavras, só: 3!") == 4


def _identity_analyzer(text):
    return [(t, t) for t in text.split()]


def test_lexical_tokens_filters_noise_stopwords_and_short_tokens():
    text = "Veja https://exemplo.org e mail@x.com: Os 2 rios da Bahia, um rio!"
    tokens = lexical_tokens(text, _identity_analyzer, frozenset({"os", "da", "um", "veja"}))
    assert tokens == ["rios", "bahia", "rio"]


def test_lexical_tokens_split_contraction_lemmas():
    def analyzer(text):
        return [("pelos", "por o"), ("jardins", "jardim")]
    assert lexical_tokens("pelos jardins", analyzer, frozenset({"por"})) == ["jardim"]


def test_remove_noise_and_semantic_profile():
    assert remove_noise("Olá, mundo! 123 _x_") == "Olá mundo x"
    assert semantic_text("  Texto\t com\u0007 ruído \n") == "Texto com ruído"
