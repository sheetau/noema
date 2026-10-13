from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_described_prescriptions import (
    truth_checks, binding_checks, description_checks, conflicting_checks, limits_checks, alignment,
)
from scripts.compose_described_prescriptions import ROOT, PARENT, generic_composed, source_composed


def test_adoption_role_condition_and_goal_do_not_collapse_into_one_truth():
    rows = truth_checks()
    assert len(rows) == 32
    for row in rows:
        adopted, active, compliant, violated = row['result']
        assert compliant != violated if active else not compliant and not violated
        assert adopted == row['adopted']
    assert any(row['adopted'] and not row['condition'] and row['result'] == [True, False, False, False] for row in rows)


def test_rule_source_role_descriptions_sign_and_context_remain_bound():
    rows = binding_checks()
    assert len(rows) == 10
    assert rows['baseline'] == [True, True, True, False]
    assert rows['holder'] == rows['held_role'] == [True, False, False, False]
    assert rows['source'] == rows['polarity'] == [False, False, False, False]


def test_truth_equivalent_goals_and_conditions_remain_distinct_descriptions():
    rows = description_checks()
    assert len(rows) == 4
    assert all(row['result'] == [True, True, True, False, False] for row in rows)


def test_conflicting_prescriptions_do_not_assert_conflicting_facts():
    rows = conflicting_checks()
    assert rows[0]['result'] == [True, False, True, True, True, False]
    assert rows[1]['result'] == [True, True, False, True, False, True]


def test_description_quantification_and_transitive_quotation_limits_are_explicit():
    rows = limits_checks()
    assert 'description domain' in rows['unbounded_description_quantification_refused']
    assert rows['rule_schema_classification_can_be_mentioned_without_execution']
    assert 'disquot' in rows['quoting_applicability_with_disquotation_refused'].lower()
    parent = parse(source_composed()[0])
    quoted = parse(source_composed()[0] + 'q[e[r[p hd2]][r[p hd2]]].')
    assert quoted['declarations'] == parent['declarations']


def test_nominal_reading_does_not_claim_the_entire_sentence_or_word_is_complete():
    row = alignment()
    assert row['source'] == 'Satzungen'
    assert row['word_meaning_not_complete'] and not row['full_semantic_equivalence']
    assert 'Formeln' in row['remaining']


def test_existing_linked_draft_and_semantic_basis_remain_intact():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse(source_composed()[0])
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert child['statements'] == parent['statements']
    for builder, counts in ((generic_composed, (1, 4)), (source_composed, (178, 243))):
        text, basis = builder()
        audit = audit_basis(parse(text), basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
