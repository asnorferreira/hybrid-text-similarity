import pytest

from hts_core.domain.text import split_sentences


@pytest.mark.parametrize("first,second", [
    ("Visite exemplo.com.", "Próxima frase."),
    ("Envie para [pessoa@dominio.com](mailto:pessoa@dominio.com).", "Depois confirme."),
    ("A versão é v1.2.", "Próxima frase."),
    ("Envie para pessoa@dominio.com.", "Depois confirme."),
    ("Visite https://exemplo.com.", "Depois confirme."),
    ("O valor é 3.5.", "Próxima frase."),
    ('Visite "exemplo.com."', "Próxima frase."),
])
def test_period_in_token_does_not_hide_sentence_end(first, second):
    assert split_sentences(first + " " + second) == [first, second]


@pytest.mark.parametrize("text,expected", [
    ("O Dr. Silva chegou. Depois saiu.", ["O Dr. Silva chegou.", "Depois saiu."]),
    ("A Profa. Lima veio. Fim.", ["A Profa. Lima veio.", "Fim."]),
    ("J. R. R. Tolkien escreveu. Depois publicou.",
     ["J. R. R. Tolkien escreveu.", "Depois publicou."]),
    ("A empresa S.A. Brasileira chegou. Fim.", ["A empresa S.A. Brasileira chegou.", "Fim."]),
    ("Nos E.U.A. Existem estados. Fim.", ["Nos E.U.A. Existem estados.", "Fim."]),
    ("Veja p.ex. Silva e Lima. Fim.", ["Veja p.ex. Silva e Lima.", "Fim."]),
    ("A tese, s.m.j. Continua válida. Fim.", ["A tese, s.m.j. Continua válida.", "Fim."]),
    ("É 3.5 vezes maior. Fim.", ["É 3.5 vezes maior.", "Fim."]),
    ('Acabou?! "Sim!" Depois saiu.', ['Acabou?!', '"Sim!"', 'Depois saiu.']),
])
def test_abbreviations_initials_decimals_and_punctuation_still_work(text, expected):
    assert split_sentences(text) == expected
