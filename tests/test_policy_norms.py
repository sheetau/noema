import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from noema.semantics import SemanticError
from scripts.check_policy_norms import REPORT, build_report
from scripts.compose_policy_norms import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_target_validity_and_polarity_do_not_collapse_requirement_permission_and_fulfillment(result):
    assert result['generic'] == {'polarity_and_validity_cases': 128, 'binding_length_cases': 48}


def test_outer_and_inner_sources_people_and_roles_keep_their_own_bindings(result):
    rows = result['references']['cases']
    assert len(rows) == 16
    assert rows['baseline'] == [True, True]
    assert rows['no_requirement'] == [False, True]
    assert rows['no_permission'] == [True, False]
    assert all(row == [False, False] for name, row in rows.items() if name not in ('baseline', 'no_requirement', 'no_permission'))
    assert result['references']['all_inner_norms_execution_and_public_classification_guarded']
    assert result['references']['unassessed_outer_requirement_refused']


def test_a_requirement_for_permission_does_not_make_the_permission_true(result):
    assert result['fulfillment']['cases'] == {
        '00': [False, False, True, False], '01': [False, False, True, True],
        '10': [True, True, True, False], '11': [True, False, True, True]}


def test_policy_adapters_preserve_the_existing_meaning_and_reject_wrong_arity(result):
    assert result['fulfillment']['policy_adapter_arity_cases'] == {
        '0': [False, False], '2': [False, False], '3': [True, True], '4': [False, False]}
    assert result['fulfillment']['private_policy_cases'] == {'0': [True, False], '1': [True, True]}
    assert result['fulfillment']['adapter_matches_existing_public_permission_content']


def test_one_norm_interface_can_also_use_two_argument_action_targets(result):
    rows = result['action_correspondence']
    assert rows['cases'] == {'00': [False, False], '01': [False, False], '10': [True, True], '11': [False, False]}
    assert rows['permission_does_not_evaluate_execution']
    assert rows['norm_interpretations_explicitly_correspond_not_automatically_identified']
    assert rows['action_adapter_cases'] == {'correct': [True], 'reordered': [False], 'empty': [False], 'missing': [False], 'extra': [False]}


def test_norm_references_remain_quotable_while_fulfillment_cannot_hide_disquotation():
    text = generic_composed()[0]
    parse(text + 'q[e[r[p rds]][r[p rds]]].')
    with pytest.raises(SemanticError, match='disquote-free'):
        parse(text + 'q[e[r[p rdw]][r[p rdw]]].')


def test_existing_definitions_and_claims_are_preserved_without_new_actual_policies():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 6)), (source_composed, (248, 437))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15


def test_saved_report_is_reproduced_without_claiming_full_source_completion(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert len(result['alignment']['segments']) == 2
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
