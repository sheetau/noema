import pytest

from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_controlled_gait import generic_checks, general_laws, source_checks, alignment
from scripts.compose_controlled_gait import ROOT, PARENT, generic_composed, source_composed


@pytest.fixture(scope='module')
def generic_result():
    return generic_checks()


def test_control_is_required_at_every_phase_not_just_the_endpoints(generic_result):
    assert generic_result['truth_cases'] == 256
    assert generic_result['accepted_truth_cases'] == 1


def test_nonempty_extended_completed_scope_and_same_participants_are_required(generic_result):
    rows = generic_result['scope_and_binding_cases']
    assert len(rows) == 16
    assert all(row == [False] for row in rows.values())


def test_full_control_has_general_completion_laws_and_rejects_weaker_conditions():
    rows = general_laws()
    assert sum(row['status'] == 'valid' for row in rows.values()) == 4
    assert rows['two_controlled_endpoints_are_enough']['countermodel_found']
    assert rows['no_fall_is_enough']['countermodel_found']


def test_literal_gait_keeps_its_scope_without_becoming_intellectual_independence():
    rows = source_checks()
    assert len(rows) == 16
    assert rows['baseline'] == rows['external_support'] == [True, True, True]
    assert rows['no_achievement'] == [True, True, False]
    assert rows['no_walk'] == rows['no_balance'] == [False, False, True]
    assert rows['future_completion'] == [False, False, True]
    assert [key for key, row in rows.items() if row[1]] == ['baseline', 'external_support', 'no_achievement']


def test_only_the_bodily_phrase_is_aligned_and_metaphor_and_concession_are_pending():
    row = alignment()
    assert row['source'] == 'einen sicheren Gang zu thun'
    assert not row['full_semantic_equivalence']
    assert 'stable intellectual activity as metaphor target' in row['remaining']
    assert 'dennoch concession and Daher inference' in row['remaining']


def test_prior_source_claims_and_definitions_are_preserved_without_literalizing_the_metaphor():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, expected in ((generic_composed, (0, 5)), (source_composed, (220, 342))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == expected
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    assert len(doc['statements']) == 13
