import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_temporal_norms import REPORT, build_report
from scripts.compose_temporal_norms import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_temporal_quantification_cannot_be_moved_through_the_normative_requirement(result):
    rows = result['requirements']['truth_table']
    assert len(rows) == 16
    assert {tuple(row['results']) for row in rows} == {(False, False), (False, True), (True, False), (True, True)}
    assert result['requirements']['inner_permissions_always_guarded']


def test_a_requirement_can_reference_a_period_without_evaluating_it(result):
    assert result['requirements']['whole_period_requirement_does_not_evaluate_its_frame']
    assert result['requirements']['unassessed_requirement_refused']
    for name in ('empty_scope', 'gap', 'scope_outside', 'empty_history', 'cyclic_order'):
        assert result['requirements']['contrasts'][name] == [True, False]


def test_period_identity_and_requirement_context_do_not_transfer(result):
    rows = result['requirements']['contrasts']
    assert rows['other_required_frame'] == rows['other_requirement_context'] == [False, True]
    assert rows['wrong_inner_source'] == [False, False]


def test_endpoint_permission_cannot_hide_a_middle_failure(result):
    rows = result['permissions']['truth_table']
    assert len(rows) == 8
    gap = next(row for row in rows if row['point_permissions'] == [True, False, True])
    assert gap['results'] == [True, False, True]
    assert sum(row['results'][1] for row in rows) == 1


def test_invalid_or_empty_period_is_not_vacuously_satisfied(result):
    rows = result['permissions']['contrasts']
    for name in ('empty_scope', 'gap', 'scope_outside', 'cyclic_order'):
        assert rows[name] == [True, False, True]
    assert rows['no_requirement_but_permissions'] == [False, True, False]
    assert rows['no_requirement_and_no_permissions'] == [False, False, False]


def test_the_selected_period_is_fixed_at_the_evaluation_context_but_still_needs_source_justification(result):
    rows = result['permissions']['contrasts']
    assert rows['different_scope_in_other_contexts'] == [True, False, True]
    assert rows['narrowed_to_first'] == [True, True, False]
    assert result['permissions']['a_narrowed_period_is_not_proof_of_source_scope_completeness']
    assert result['permissions']['all_world_situations_are_not_automatically_target_times']


def test_existing_temporal_and_normative_definitions_are_reused_without_rewriting_old_claims():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 443)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text


def test_saved_report_is_reproduced_without_claiming_full_freedom_or_a_unique_reading(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
