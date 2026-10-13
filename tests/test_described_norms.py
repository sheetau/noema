import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from noema.semantics import SemanticError
from scripts.check_described_norms import REPORT, build_report
from scripts.compose_described_norms import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_both_polarities_of_requirements_permissions_and_performance_are_distinct(result):
    assert result['generic']['polarity_state_cases'] == 64
    assert result['generic']['norms_without_execution_assessment']
    assert result['generic']['unassessed_fulfillment_refused']


def test_source_person_role_activity_description_and_context_are_all_bound(result):
    rows = result['generic']['binding_cases']
    assert len(rows) == 6
    assert all(row == [False, False, False, True, False] for row in rows.values())
    assert result['generic']['equal_contents_with_distinct_descriptions'] == [True, True]


def test_old_permission_spreads_to_equal_content_but_new_permission_stays_with_the_action(result):
    rows = result['source_cases']['cases']
    assert rows['baseline'] == [True, True, True, False, False, True, True]
    assert rows['only_second'] == [True, True, False, True, False, True, True]
    assert rows['both_allowed'] == [True] * 7


def test_one_forbidden_action_does_not_remove_the_other_actions_permission(result):
    assert result['source_cases']['cases']['both_allowed_one_forbidden'] == [False, False, False, True, False, True, True]


def test_no_public_activities_is_vacuous_permission_not_an_actual_publication(result):
    rows = result['source_cases']['cases']
    assert rows['no_public_activities'] == [False, False, False, False, True, True, True]
    assert rows['no_private_prohibition'] == [True, True, True, False, False, False, True]


def test_execution_aliases_sources_and_contexts_do_not_transfer_norms(result):
    rows = result['source_cases']['cases']
    assert rows['different_execution_description'] == [True, True, False, False, False, False, True]
    for name in ('wrong_source', 'wrong_context'):
        assert rows[name] == [False, False, False, False, False, False, True]
    assert result['source_cases']['new_permission_does_not_evaluate_old_norms_or_execution']
    assert result['source_cases']['unknown_described_permission_refused']


def test_permission_is_quotable_but_fulfillment_cannot_hide_disquotation():
    text = generic_composed()[0]
    parse(text + 'q[e[r[p rdm]][r[p rdm]]].')
    with pytest.raises(SemanticError, match='disquote-free'):
        parse(text + 'q[e[r[p rdq]][r[p rdq]]].')


def test_old_definitions_and_claims_remain_available_for_explicit_comparison():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 5)), (source_composed, (246, 422))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_saved_report_is_reproduced_without_claiming_the_full_freedom_clause(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert len(result['source_cases']['cases']) == 10
    assert len(result['alignment']['segments']) == 2
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
