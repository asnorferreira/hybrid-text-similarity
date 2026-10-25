from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class Ancestor(Strict):
    source_id: str = Field(min_length=1)
    sentence_id: str = Field(min_length=1)


class SentenceRecord(Strict):
    id: str = Field(min_length=1)
    position: int = Field(ge=0)
    text: str = Field(min_length=1)
    semantic: str
    lexical: list[str]
    words: int = Field(ge=0)
    ancestors: list[Ancestor]
    transformation: str
    parameters: dict
    intended_class: str | None
    validated_class: str | None
    semantic_target: float | None
    validation: Literal['structural', 'human_pending', 'ambiguous']


class Source(Strict):
    id: str
    title: str
    url: str
    provider: str
    pageid: int
    revision: int
    collected_utc: str = Field(min_length=10)
    license: str
    license_reference: str
    license_status: Literal['historical_declared', 'source_verified', 'fixture']
    history_url: str
    raw_file: str
    raw_sha256: str
    extracted_file: str
    extracted_sha256: str
    normalized_file: str
    normalized_sha256: str
    text: str
    language: Literal['pt-BR-expected']
    extraction: str
    theme: str
    theme_origin: str
    inclusion: Literal['included']
    inclusion_reason: str
    exposure: str
    group: str
    split: Literal['train', 'validation', 'test']
    sentences: list[SentenceRecord] = Field(min_length=1)
    provenance_verification: dict | None = None


class Fraction(Strict):
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)

    @model_validator(mode='after')
    def bounded(self):
        if self.numerator > self.denominator:
            raise ValueError('fração acima de um')
        return self


class Pair(Strict):
    id: str
    content_id: str
    source_id: str
    source_ids: list[str] = Field(min_length=1)
    split: Literal['train', 'validation', 'test']
    synthetic_type: Literal['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7']
    method: str
    severity: str
    seed: int
    text: str = Field(min_length=1)
    sentences: list[SentenceRecord] = Field(min_length=1)
    r: Fraction
    r_by_source: dict[str, Fraction]
    generation: dict
    human_review: Literal['pending', 'not_performed']
    content_assessment: dict | None = None


class Format(Strict):
    content_id: str
    family_ids: list[str]
    split: Literal['train', 'validation', 'test']
    kind: Literal['pdf', 'docx', 'txt']
    file: str
    sha256: str
    extracted: str
    expected: str
    roundtrip: bool
    container: dict
