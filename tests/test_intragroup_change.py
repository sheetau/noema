import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_intragroup_change import REPORT, build_report
from scripts.compose_intragroup_change import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_change_requires_assessment_and_opposite_endpoint_states(result):
    rows = result['generic']
    assert rows['state_cases'] == 64
    assert rows['accepted_states'] == 1


def test_membership_alone_cannot_replace_a_causal_activity_in_the_same_process(result):
    rows = result['generic']
    assert rows['activity_cases'] == 512
    assert rows['accepted_activities'] == 1
    bindings = rows['binding_and_history_cases']
    assert len(bindings) == 24
    assert [name for name, value in bindings.items() if value == [True]] == ['whole_as_part']


def test_developmental_assistance_is_separate_from_dependence_in_the_result(result):
    rows = result['source_cases']['cases']
    assert rows['baseline'] == rows['external_assistance'] == [True, True]
    assert rows['guided_outcome'] == [False, False]
    assert result['source_cases']['other_group_members_need_not_acquire_capacity']


def test_existential_participants_cannot_escape_the_same_group_and_causal_part(result):
    rows = result['source_cases']['cases']
    assert len(rows) == 20
    assert [name for name, value in rows.items() if value == [True, True]] == [
        'baseline', 'external_assistance', 'whole_as_part']
    assert all(value[0] == value[1] for value in rows.values())


def test_previous_claims_are_preserved_without_asserting_actual_public_enlightenment():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 3)), (source_composed, (226, 376))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_partial_component_does_not_count_as_a_completed_source_unit(result):
    assert result['alignment']['unit'] == 'kant-1784:u0011'
    assert result['alignment']['source'] == 'sich selbst aufkläre'
    assert not result['alignment']['full_semantic_equivalence']
    assert result['alignment']['remaining']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result['new_source_assertions'] == 0


def test_saved_report_is_reproduced_from_executed_definitions(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
