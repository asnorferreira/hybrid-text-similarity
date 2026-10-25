from copy import deepcopy

import pytest

from hts_core.adapters.dataset_curation import curated_text
from hts_core.adapters.dataset_operational import check_generated_policy, verify_generated_coverage
from hts_core.adapters.dataset_review import assessment_state
from hts_core.adapters.dataset_store import read_json
from tests.test_dataset_s4 import CORE


def policy():
    return deepcopy(read_json(CORE/'configs/dataset_operational.json')['generated_policy'])


@pytest.mark.parametrize('value', [None, 0, -1, True, False, '2', 1.5])
def test_minimum_strict_positive_integer(value):
    config = policy()
    config['minimum_pairs_per_method_split_theme'] = value
    with pytest.raises(ValueError, match='minimum_pairs'):
        check_generated_policy(config)


def test_minimum_required():
    config = policy()
    del config['minimum_pairs_per_method_split_theme']
    with pytest.raises(ValueError, match='obrigatórios'):
        check_generated_policy(config)


@pytest.mark.parametrize('field,value', [
    ('source_sentences', True), ('source_sentences', 0), ('c6_sentences', 2),
    ('attempts_per_item', 2), ('maximum_sources', -1), ('maximum_records', '37'),
    ('selection', 'ignored'), ('methods', ['llm_direct', 'llm_direct'])])
def test_other_declared_policy_fields_are_checked(field, value):
    config = policy()
    config[field] = value
    with pytest.raises(ValueError):
        check_generated_policy(config)


@pytest.mark.parametrize('actual,minimum,valid', [(1, 2, False), (2, 2, True), (3, 2, True)])
def test_minimum_counts_every_cell(actual, minimum, valid):
    config = policy()
    config['minimum_pairs_per_method_split_theme'] = minimum
    sources = [{'id': split, 'theme': 'tema', 'split': split} for split in ('train', 'validation', 'test')]
    pairs = [{'id': f'{split}:{method}:{i}', 'source_id': split, 'split': split,
              'synthetic_type': 'C5' if method != 'phrase_guided_rewrite' else 'C6', 'method': method}
             for split in ('train', 'validation', 'test') for method in config['methods'] for i in range(actual)]
    if valid:
        counts = verify_generated_coverage(sources, pairs, config, 'fixture', 'operational_derivation')
        assert len(counts) == 9 and set(counts.values()) == {actual}
    else:
        with pytest.raises(ValueError, match='mínimo=2, real=1; versão=fixture'):
            verify_generated_coverage(sources, pairs, config, 'fixture', 'operational_derivation')


def test_duplicate_pair_never_counts_twice():
    pair = {'id': 'same'}
    with pytest.raises(ValueError, match='duplicados'):
        verify_generated_coverage([], [pair, pair], policy(), 'fixture', 'operational_derivation')


def test_assessment_has_individual_scope_and_reference():
    review = {'responses': [{'id': 'reviewed', 'decision': 'accept'}], 'modality': 'automated_ai',
              'identity': 'hash', 'dataset_version': 'candidate'}
    assert assessment_state('unseen', review) == assessment_state('unseen')
    assert assessment_state('unseen')['status'] == 'not_assessed'
    assert assessment_state('reviewed', review) == {
        'status': 'accept', 'scope': 'whole_pair_not_individual_sentences', 'modality': 'automated_ai',
        'review_identity': 'hash', 'review_dataset_version': 'candidate', 'response_id': 'reviewed'}


@pytest.mark.parametrize('raw,expected', [
    ('O pico tem {{Fmtn|4810,45}} m de altitude.', 'O pico tem 4810,45 m de altitude.'),
    ('A área vai de {{fmtn|1800000}} a {{fmtn|1942500|km²}}.', 'A área vai de 1800000 a 1942500 km².'),
    ('Surgiu no {{séc|XVI|x}} e no {{séc|XVIII}}.', 'Surgiu no século XVI e no século XVIII.'),
    ('A {{PEPB|aguarela|aquarela}} preserva a água.', 'A aquarela preserva a água.'),
    ('A arqueia<sup>[[AO 1990]]</sup> é unicelular.', 'A arqueia é unicelular.'),
    ('O {{PBPE|Deserto do Saara|Deserto do Sara}} é quente.', 'O Deserto do Saara é quente.'),
    ('{{-fim}}\nA arquitetura surgiu no {{séc|XII}}.', 'A arquitetura surgiu no século XII.'),
    ('{{Imagem múltipla|image1=exemplo.jpg}}\nO ritmo surgiu em Pernambuco.', 'O ritmo surgiu em Pernambuco.'),
    ('O nome vem de {{Lang|la|cellula}}.', 'O nome vem de cellula.'),
    ('O rio [[Ásia|asiático]] contém 長江, α, 3,5 km² (área).', 'O rio asiático contém 長江, α, 3,5 km² (área).'),
    ('Uma frase {{desconhecido|123}} não é recuperável. Outra frase limpa permanece aqui.', 'Outra frase limpa permanece aqui.'),
])
def test_curated_literal_raw_oracles(raw, expected):
    assert curated_text(raw)[0] == expected


def test_pdf_mixed_scripts_preserves_literal_content():
    from hts_core.adapters.dataset_formats import render
    from hts_core.adapters.parsers import parse_document
    text = 'A região conserva الصحراء الكبرى, 長江, α, 4810,45 m e área em km².'
    data, metadata = render(text, 'pdf')
    assert parse_document('fixture.pdf', data) == text
    assert metadata['arabic_font_sha256'] == '6f611412270a132bbac838da9259d4c68569b4175f3b3b8fa3fa36a30b56dab9'
    assert 'not implemented' in metadata['arabic_presentation']


def test_cjk_asset_is_regular_static_not_default_hairline():
    import struct
    data = (CORE/'assets/fonts/NotoSansCJKsc-Regular-HTS.ttf').read_bytes()
    count = struct.unpack_from('>H', data, 4)[0]
    tables = {tag: (offset, length) for tag, _, offset, length in
              (struct.unpack_from('>4sIII', data, 12 + i * 16) for i in range(count))}
    assert b'fvar' not in tables and b'glyf' in tables
    assert struct.unpack_from('>H', data, tables[b'OS/2'][0] + 4)[0] == 400
