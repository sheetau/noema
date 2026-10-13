import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_capacity_progress import REPORT, build_report
from scripts.compose_capacity_progress import ROOT, PARENT, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_raw_gain_and_assessment_validity_are_separate(result):
    assert result['finite']['property_and_assessment_cases'] == 256
    assert result['finite']['raw_count_is_not_an_assessment_certificate']
    rows = result['finite']['contrasts']
    assert rows['reordered'] == [True, True]
    for name in ('omitted_person', 'duplicate', 'empty', 'out_of_scope', 'not_later'):
        assert rows[name] == [False, True]
    assert rows['changed_scope_is_distinct_measure'] == [True, True]


def test_common_baseline_is_retained_even_when_relative_loss_is_the_same(result):
    rows = result['source']['cases']
    assert len(rows) == 17
    for name, gains in (('baseline', (1, 2)), ('one_already_capable', (0, 1)), ('both_already_capable', (-1, 0))):
        assert rows[name]['valid_bounded_comparison'] and rows[name]['qualified_policy']
        assert (rows[name]['on_gain'], rows[name]['off_gain']) == gains
        assert rows[name]['native_gains_match'] == [True, True]
    assert not rows['zero_tolerance']['valid_bounded_comparison']


def test_native_capacity_requires_assessment_and_independent_use(result):
    rows = result['source']['cases']
    for name in ('unassessed_before', 'unassessed_after', 'guided_outcome'):
        assert not rows[name]['valid_bounded_comparison']
        assert not rows[name]['qualified_policy']
    assert rows['no_methods_with_larger_tolerance']['valid_bounded_comparison']
    assert rows['no_methods_with_larger_tolerance']['on_gain'] == 0
    assert result['source']['native_capacity_definitions_not_replaced_by_primitives']
    assert result['source']['unknown_capacity_and_assessment_refused']


def test_same_nonempty_human_cohort_and_temporal_order_are_required(result):
    rows = result['source']['cases']
    for name in ('omitted_person', 'duplicate', 'empty', 'nonhuman_scope', 'not_later', 'no_solution'):
        assert not rows[name]['valid_bounded_comparison']
        assert not rows[name]['qualified_policy']


def test_qualified_policy_requires_the_same_model_and_an_actual_on_result(result):
    rows = result['source']['cases']
    for name in ('wrong_worlds', 'not_actual_policy', 'not_actual_result'):
        assert rows[name]['valid_bounded_comparison']
        assert not rows[name]['qualified_policy']
    assert result['source']['permission_does_not_evaluate_capacity']
    assert result['source']['qualified_target_roundtrips']


def test_no_new_primitive_replaces_capacity_or_adds_an_author_claim():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    text, basis = source_composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (250, 481)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 15
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    dependencies = audit['definition_dependencies']['definition_primitive_dependencies']['hzh']
    assert {'aa', 'ab', 'ac', 'ad', 'ae', 'af', 'ap', 'ha', 'hb', 'hd'} <= set(dependencies)


def test_report_reproduces_without_equating_headcount_with_complete_enlightenment(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['new_primitives'] == result['new_source_assertions'] == 0
    assert result['parent_preserved'] and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
