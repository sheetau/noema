import json

import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_count_focus import REPORT, build_report
from scripts.compose_count_focus import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_every_attainable_count_including_zero_and_the_population_size_is_generated(result):
    assert result['count_domains'] == {str(n): list(range(n + 1)) for n in (0, 1, 2, 5, 16)}


def test_true_weaker_or_equivalent_alternatives_are_not_excluded(result):
    generic = result['generic']
    assert generic['truth_table_cases'] == 192
    assert generic['contrasts']['weaker_true'] == generic['contrasts']['equivalent_true'] == [True, True]
    assert generic['contrasts']['overlapping_true'] == [False, False]
    assert generic['contrasts']['overlapping_false'] == [False, True]


def test_observed_count_alone_cannot_establish_implication(result):
    rows = result['generic']['contrasts']
    assert rows['incomplete_domain_hides_overlap'] == [True, True]
    assert rows['overlapping_true'] == [False, False]
    assert rows['actual_outside_domain'] == rows['empty_domain'] == [True, False]


def test_numeric_alternatives_never_change_the_actual_count_or_read_expectations(result):
    rows = result['source_cases']['cases']
    assert len(rows) == 8
    assert all(row[0] for row in rows.values())
    assert rows['weaker'] == rows['equivalent'] == rows['all_of_small_scope'] == [True, True]
    assert rows['overlap'] == rows['empty'] == rows['wrong_context'] == rows['wrong_size'] == [True, False]
    assert result['source_cases']['expectation_primitives_guarded_against_execution']


def test_unknown_alternative_at_an_unobserved_but_attainable_count_is_refused(result):
    assert result['source_cases']['unknown_alternative_refused']


def test_empty_alternatives_fail_but_contextual_relevance_is_not_claimed_by_the_truth_check(result):
    rows = result['generic']['contrasts']
    assert rows['empty_alternatives'] == [True, False]
    assert rows['duplicate_alternatives'] == rows['impossible_alternative'] == [False, True]
    assert not result['alignment']['full_semantic_equivalence']


def test_revised_conclusion_attribution_does_not_execute_either_counts_or_alternatives(result):
    rows = result['discourse_cases']
    assert [name for name, value in rows['cases'].items() if value == [True]] == ['baseline']
    assert rows['all_count_and_alternative_primitives_guarded_against_execution']


def test_the_old_conclusion_is_replaced_without_changing_other_claims_or_old_definitions():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 3)), (source_composed, (225, 372))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements'][:-1]
    assert parent['statements'][-1]['body']['symbol'] == 'h5u'
    assert doc['statements'][-1]['body']['symbol'] == 'h5z'
    assert len(doc['statements']) == 15


def test_saved_report_is_reproduced_from_executed_definitions(result):
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
