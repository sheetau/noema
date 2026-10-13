from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_achievement_exercise import (
    generic_checks, general_laws, source_checks, concession_checks, alignment,
)
from scripts.compose_achievement_exercise import ROOT, PARENT, generic_composed, source_composed


def test_completion_order_requires_one_person_anchor_and_history():
    result = generic_checks()
    assert result['truth_and_order_cases'] == 256
    assert result['accepted_cases'] == 10
    assert len(result['binding_cases']) == 7
    assert all(row == [False] for row in result['binding_cases'].values())


def test_general_order_laws_do_not_turn_two_experiences_into_a_causal_connection():
    rows = general_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 5
    assert rows['two_experiences_alone_suffice']['countermodel_found']
    assert rows['completion_order_implies_causation']['countermodel_found']


def test_native_join_allows_coincident_and_overlapping_work_but_rejects_reversed_order():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 13
    for name in ('baseline', 'coincident', 'straddling', 'same_process'):
        assert rows[name] == [True] * 4
    assert rows['exercise_before_achievement'] == [True, True, False, False]
    assert rows['future_exercise'] == [True, False, False, False]
    assert rows['future_achievement'] == [False, True, False, False]
    assert rows['unassessed_achievement'] == [False, True, False, False]
    assert result['bodily_gait_primitives_guarded_against_execution']


def test_concession_keeps_achievement_in_the_expected_alternative():
    rows = concession_checks()
    assert len(rows) == 9
    assert [name for name, value in rows.items() if value == [True]] == ['baseline']
    assert rows['expected_without_achievement'] == rows['expected_also_exercises'] == [False]


def test_alignment_adds_the_conjunction_and_concession_without_claiming_full_equivalence():
    row = alignment()
    assert row['source'] == 'und dennoch einen sicheren Gang zu thun'
    assert not row['full_semantic_equivalence']
    assert 'final population counting and Daher inference' in row['remaining']


def test_no_primitive_or_source_assertion_is_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 2)), (source_composed, (223, 354))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 14
