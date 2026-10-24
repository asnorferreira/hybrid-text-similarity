from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class TextInput(StrictModel):
    text: str = Field(min_length=1)


class CompareRequest(StrictModel):
    contract_version: Literal['1.0']
    source: TextInput
    suspect: TextInput
    mode: Literal['hybrid', 'lexical'] = 'hybrid'


class Index(StrictModel):
    source_to_suspect: float = Field(ge=0, le=1)
    suspect_to_source: float = Field(ge=0, le=1)
    value: float = Field(ge=0, le=100)


class SentenceInfo(StrictModel):
    index: int = Field(ge=0)
    raw: str
    semantic: str
    lexical: list[str]
    words: int = Field(ge=0)
    flags: list[str]
    window: dict[str, JsonValue] | None


class Pair(StrictModel):
    source: int = Field(ge=0)
    suspect: int = Field(ge=0)
    score: float = Field(ge=0, le=1)


class Alignment(StrictModel):
    pairs: list[Pair]
    unmatched_source: list[int]
    unmatched_suspect: list[int]
    objective: float = Field(ge=0)


class Decision(StrictModel):
    label: Literal['copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada']
    reason: str
    lexical_high: bool


class Match(StrictModel):
    source: int
    suspect: int
    lexical: float = Field(ge=0, le=1)
    semantic_raw: float = Field(ge=-1, le=1)
    semantic_operational: float = Field(ge=0, le=1)
    fused: float = Field(ge=0, le=1)
    edit: float = Field(ge=0, le=1)
    characters: dict[str, float]
    decision: Decision


class Summary(StrictModel):
    counts: dict[str, int]
    proportions: dict[str, float]
    denominator: int = Field(ge=1)
    predominance: str
    inserted_segment: Literal['indisponivel_regra_nao_definida']


UnitScore = Annotated[float, Field(ge=0, le=1)]
RawCosine = Annotated[float, Field(ge=-1, le=1)]


class Matrices(StrictModel):
    lexical: list[list[UnitScore]]
    semantic_raw: list[list[RawCosine]] | None
    semantic_operational: list[list[UnitScore]] | None
    fused: list[list[UnitScore]] | None


class Metadata(StrictModel):
    policy: Literal['q5-v2']
    config_sha256: str
    configuration: dict[str, JsonValue]
    idf: dict[str, JsonValue]
    model: dict[str, JsonValue] | None
    semantic_unavailable: str | None
    unavailable_components: list[str]
    signature: dict[str, JsonValue]


class ComparisonResult(StrictModel):
    contract_version: Literal['1.0']
    state: Literal['calculated', 'resource_unavailable']
    method: Literal['hybrid', 'lexical']
    index: Index | None
    lexical_index: Index
    semantic_index: Index | None
    matrices: Matrices
    source: list[SentenceInfo]
    suspect: list[SentenceInfo]
    matches: list[Match] | None
    alignment: Alignment | None
    summary: Summary | None
    metadata: Metadata


class ApiError(StrictModel):
    contract_version: Literal['1.0'] = '1.0'
    state: Literal['invalid_input', 'unsupported_format', 'extraction_failed', 'no_useful_content', 'resource_unavailable']
    detail: str


class Extraction(StrictModel):
    contract_version: Literal['1.0']
    text: str
