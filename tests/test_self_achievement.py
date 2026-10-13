import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_self_achievement import generic_checks, source_checks, alignment
from scripts.compose_self_achievement import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def generic_result():
    return generic_checks()


@pytest.fixture(scope='module')
def native_result():
    return source_checks()


def test_self_achievement_needs_the_state_change_and_agent_bound_causal_work(generic_result):
    assert generic_result['truth_cases'] == 1024
    assert generic_result['accepted_truth_cases'] == 1


def test_other_people_processes_times_and_result_descriptions_do_not_supply_the_change(generic_result):
    rows = generic_result['binding_and_history_cases']
    assert len(rows) == 21
    assert all(result == [False] for result in rows.values())


def test_past_success_is_not_current_permanence_or_future_success(native_result):
    assert len(native_result) == 20
    assert native_result['baseline'] == native_result['later_loss'] == [True] * 4
    assert native_result['future_achievement'] == [False, False, True, False]
    for name in ('already_capable', 'no_self_work', 'other_agent', 'other_mind', 'unrelated_work',
                 'no_causal_result', 'wrong_result_description', 'guided_outcome'):
        assert native_result[name] == [False, False, True, False]


def test_incomplete_assessment_does_not_lower_counts_but_a_valid_witness_is_enough(native_result):
    assert native_result['unassessed_before'] == native_result['unassessed_after'] == [False] * 4
    assert native_result['other_unassessed'] == [True, True, False, False]
    assert native_result['unassessed_current_after_success'] == [True] * 4
    assert native_result['other_unassessed_future'] == [True] * 4


def test_only_partial_self_achievement_is_aligned_without_secure_gait_or_conclusion():
    row = alignment()
    assert row['source'].startswith('denen es gelungen ist')
    assert row['source'].endswith('Unmündigkeit heraus zu wikkeln')
    assert 'dennoch' not in row['source']
    assert 'secure gait and concession' in row['remaining']
    assert not row['full_semantic_equivalence']


def test_basis_counts_and_previous_claims_remain_exact():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 3)), (source_composed, (217, 339))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 13
