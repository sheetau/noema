import json

import pytest

from noema.grammar import parse
from scripts.check_office_speech import REPORT, build_report
from scripts.compose_office_speech import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_required_duty_and_public_speech_are_independent_of_performance(result):
    rows = result['finite']['state_cases']
    assert len(rows) == 32
    for row in rows:
        required, allowed, forbidden, duty_done, speech_done = row['states']
        assert row['results'] == [required, allowed and not forbidden,
            required and allowed and not forbidden, required and not duty_done, speech_done]
    assert result['finite']['norms_do_not_evaluate_execution']
    assert result['finite']['unknown_execution_and_norms_refused']


def test_role_and_target_mismatches_do_not_erase_the_other_activity(result):
    rows = result['finite']['binding_contrasts']
    assert len(rows) == 17
    for name in ('issuer', 'duty_person', 'duty_role', 'duty_activity', 'duty_context',
                 'duty_description', 'no_entrusted_office'):
        assert rows[name] == [False, True, False, False, False]
    for name in ('authority', 'speech_person', 'speech_role', 'speech_activity', 'speech_context',
                 'speech_is_official', 'private_audience', 'missing_reader', 'message_description'):
        assert rows[name] == [True, False, False, True, False]


def test_pair_requires_two_activities_even_if_each_has_the_relevant_norm(result):
    assert result['finite']['binding_contrasts']['same_activity'] == [True, True, False, True, False]


def test_same_composition_accepts_a_nonmilitary_interpretation(result):
    assert result['finite']['laboratory_interpretation'] == [True, True, True, True, False]


def test_parent_and_its_author_claims_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    audit = result['documents'][basis['document']]
    assert (audit['primitive_count'], audit['definition_count']) == (250, 495)
    assert result['new_primitives'] == result['new_source_assertions'] == 0


def test_report_reproduces_and_partial_alignment_is_not_completion(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
