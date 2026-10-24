import re
import unicodedata

SOFT_HYPHEN = "­"

_LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl"}
_SOFT_BREAK = re.compile(SOFT_HYPHEN + r"[ \t]*\n[ \t]*")
_HARD_BREAK = re.compile(r"([^\W\d_]+)[-‐][ \t]*\n[ \t]*([^\W\d_]+)")
PRESERVED_COMPOUNDS = frozenset({"guarda-chuva", "segunda-feira", "terça-feira", "quarta-feira",
                                 "quinta-feira", "sexta-feira", "bem-estar", "fazê-lo"})
_PARAGRAPH = re.compile(r"\n[ \t]*\n+")
_SPACES = re.compile(r"\s+")
_CONTROL = re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]")


def _join_hard_break(match: re.Match) -> str:
    left, right = match.group(1), match.group(2)
    compound = left + "-" + right
    if compound.casefold() in PRESERVED_COMPOUNDS or not right[0].islower():
        return compound
    return left + right


def clean_extracted(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = unicodedata.normalize("NFC", text)
    for ligature, plain in _LIGATURES.items():
        text = text.replace(ligature, plain)
    text = _CONTROL.sub(" ", text)
    text = _SOFT_BREAK.sub("", text)
    text = text.replace(SOFT_HYPHEN, "")
    while _HARD_BREAK.search(text):
        text = _HARD_BREAK.sub(_join_hard_break, text)
    paragraphs = (_SPACES.sub(" ", p).strip() for p in _PARAGRAPH.split(text))
    return "\n\n".join(p for p in paragraphs if p)


ABBREVIATIONS = frozenset({
    "sr", "sra", "srs", "sras", "dr", "dra", "drs", "dras", "prof", "profa", "profs", "eng", "arq",
    "av", "art", "arts", "cap", "caps", "fig", "figs", "tab", "vol", "vols", "p", "pp", "pág", "págs",
    "ed", "eds", "al", "ex", "n", "nº", "núm", "obs", "séc", "tel", "cf", "op", "cit", "ltda", "cia",
    "jr", "min", "máx", "aprox", "inc", "dep", "gov", "s", "v", "vs",
    "p.ex", "s.m.j", "e.g", "i.e", "a.c", "d.c",
})

_SENTENCE_END = re.compile(r"[.!?…]+[\"”’»)\]]*\s+")
_OPENERS = "\"“‘«(["


def _ends_with_abbreviation(prefix: str) -> bool:
    match = re.search(r"(\S+)$", prefix)
    if not match:
        return False
    word = match.group(1).lstrip(_OPENERS)
    if re.fullmatch(r"\d+(?:[.,]\d+)+", word):
        return False
    initials = word.split(".")
    if len(initials) > 1 and all(len(part) == 1 and part.isalpha() and part.isupper() for part in initials):
        return True
    if len(word) == 1 and word.isupper():
        return True
    return word.lower() in ABBREVIATIONS


def split_sentences(text: str) -> list[str]:
    sentences = []
    for paragraph in text.split("\n\n"):
        start = 0
        for match in _SENTENCE_END.finditer(paragraph):
            following = paragraph[match.end():].lstrip(_OPENERS)[:1]
            if not following or not (following.isupper() or following.isdigit()):
                continue
            if match.group(0)[0] == "." and _ends_with_abbreviation(paragraph[start:match.start()]):
                continue
            sentence = paragraph[start:match.end()].strip()
            if sentence:
                sentences.append(sentence)
            start = match.end()
        tail = paragraph[start:].strip()
        if tail:
            sentences.append(tail)
    return sentences


def word_count(sentence: str) -> int:
    return len(re.findall(r"[^\W_]+", sentence))
