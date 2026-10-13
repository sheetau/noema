from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_learned_familiarity import (
    generic_checks, movement_checks, source_checks, attribution_checks, alignment,
)
from scripts.compose_learned_familiarity import ROOT, PARENT, generic_composed, source_composed


def test_experience_retained_contribution_and_settled_response_are_separate_from_capacity():
    rows = generic_checks()['truth_cases']
    assert len(rows) == 16
    # Every combination of current familiarity and independent capacity is possible.
    assert {(row['results'][1], row['results'][4]) for row in rows} == {
        (False, False), (False, True), (True, False), (True, True)}
    assert any(row['results'][3] and row['results'][2] for row in rows)
    assert all(not row['results'][1] or row['results'][3] for row in rows)
    assert all(row['results'][1] != row['results'][2] for row in rows)


def test_unknown_history_is_not_negative_familiarity_and_activity_descriptions_stay_unexecuted():
    report = generic_checks()
    assert report['unknown_experience_refused'] and report['description_unexecuted']
    rows = report['binding_and_history_cases']
    assert len(rows) == 18
    assert not any(row[1] for row in rows.values())
    assert all(rows[name][:4] == [False] * 4 for name in ('missing_now', 'empty_history', 'cyclic_order'))
    assert rows['present_experience'][3] is False
    assert rows['future_experience'][3] is False


def test_body_movement_binds_its_own_person_limb_activity_and_context():
    rows = movement_checks()
    assert len(rows) == 7
    assert [key for key, row in rows.items() if not row[0]] == ['no_movement', 'blocked']


def test_reason_retains_the_same_person_activity_description_and_hypothetical_case():
    rows = source_checks()
    assert len(rows) == 15
    assert rows['baseline'] == [False, True, True, True, True]
    assert rows['familiar'] == [True, False, True, False, False]
    assert rows['no_experience'] == [False, True, False, True, True]
    assert rows['wrong_anchor'][-1] is False
    assert [key for key, row in rows.items() if row[-1]] == ['baseline', 'no_experience', 'different_activity']


def test_attributed_reason_is_not_a_fact_assertion_or_reversed_discourse_order():
    report = attribution_checks()
    assert report['content_unexecuted']
    assert len(report['cases']) == 6
    assert [key for key, row in report['cases'].items() if row[0]] == ['baseline']


def test_reason_alignment_excludes_the_following_consequence_and_retains_unresolved_readings():
    row = alignment()
    assert row['source'] == 'weil er zu dergleichen freier Bewegung nicht gewöhnt ist.'
    assert not row['full_semantic_equivalence']
    assert 'dergleichen activity-kind reference' in row['remaining']
    assert 'present-tense projection versus hypothetical reason' in row['remaining']


def test_source_basis_and_parent_are_preserved_without_new_grammar():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 8)), (source_composed, (210, 313))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    assert doc['schema_version'] == parent['schema_version']
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'][:-1] == parent['statements']
    assert len(doc['statements']) == 13
    assert doc['statements'][-1]['body']['symbol'] == 'h3t'
