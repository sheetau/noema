import json

import pytest

from noema.grammar import parse
from scripts.check_compact_library import REPORT, build_report
from scripts.compose_compact_library import ROOT, PARENT, composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_same_author_statements_and_requested_definitions_have_a_smaller_bundle(result):
    assert result['source_characters'] == 81515
    compact = result['sizes']['kant-compact-library']
    assert (compact['characters'], compact['declarations'], compact['statements']) == (35908, 429, 15)
    source = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, _, extracted = composed()
    assert parse(text)['statements'] == source['statements']
    retained = set(extracted.retained_symbols)
    assert extracted.document['declarations'] == [d for d in source['declarations'] if d['name'] in retained]
    assert set(result['roots']) <= retained


def test_small_library_drops_claims_only_when_explicitly_requested(result):
    core = result['sizes']['public-speech-core']
    assert (core['characters'], core['declarations'], core['statements']) == (3434, 42, 0)
    audit = result['documents']['examples/v014/public-speech-core.noema']
    assert (audit['primitive_count'], audit['definition_count']) == (19, 23)


def test_evaluation_and_unknown_refusal_behavior_match_existing_examples(result):
    assert len(result['replays']) == 3
    for replay in result['replays'].values():
        assert replay['matching_evaluations'] > 30
        assert replay['matching_refusals'] >= 2


def test_report_reproduces_without_treating_bundle_size_as_translation_accuracy(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips']
    assert result['names_aliases_and_quoted_syntax_preserved']
    assert result['all_original_statements_preserved_in_compact_document']
    assert not result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
