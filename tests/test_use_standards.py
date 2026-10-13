from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_use_standards import (
    evidence_checks, scope_checks, binding_checks, purpose_checks, bridge_checks, general_laws,
)
from scripts.compose_use_standards import ROOT, PARENT, generic_composed, source_composed


def test_complete_evidence_decides_use_but_conflicts_never_do():
    rows = evidence_checks()
    assert len(rows) == 64
    for row in rows:
        active, complete, proper, violation, conflict, gap = row['result']
        if complete:
            assert proper != violation
            assert not conflict and not gap
        if conflict:
            assert active and not proper and not violation and not complete
        if not active:
            assert not any(row['result'])


def test_missing_information_is_not_misuse_and_known_violation_survives_other_gaps():
    rows = evidence_checks()
    assert any(row['result'] == [True, False, False, False, False, True] for row in rows)
    assert any(row['result'] == [True, False, False, True, False, True] for row in rows)
    assert any(row['result'] == [True, True, False, True, False, False] for row in rows)


def test_empty_and_inapplicable_criteria_cannot_supply_vacuous_approval():
    rows = scope_checks()
    assert len(rows) == 16
    assert all(not any(row['result']) for row in rows if not set(row['members']) & set(row['applicable']))
    # Excluding the failed criterion yields a positive assessment only of the
    # explicitly reduced standard, not the original two-criterion standard.
    assert any(row['members'] == ('c1',) and row['result'][2] for row in rows)
    assert any(row['members'] == ('c1', 'c2') and row['applicable'] == ('c1', 'c2') and row['result'][3] for row in rows)


def test_other_people_resources_acts_standards_or_contexts_do_not_supply_grounds():
    rows = binding_checks()
    assert len(rows) == 16
    assert all(not result[-1] for result in rows.values())
    assert all(result[5] and not result[3] for key, result in rows.items() if key.startswith('evidence_'))


def test_success_does_not_entail_proper_use_and_failure_does_not_entail_violation():
    report = purpose_checks()
    rows = report['independence']
    assert len(rows) == 32
    assert any(row['attained'] and row['violation'] for row in rows)
    assert any(not row['attained'] and row['proper'] for row in rows)
    assert len(report['bindings']) == 9
    assert report['equal_content_alias_kept_distinct']


def test_candidate_grounds_are_not_silently_identified_with_kant_appraisal():
    rows = bridge_checks()
    assert [row['appraisal'] for row in rows if row['bridge']] == [(True, False)]


def test_assessment_laws_hold_beyond_finite_criterion_and_context_samples():
    rows = general_laws()['claims']
    assert sum(row['status'] == 'valid' for row in rows.values()) == 5
    assert sum(row['countermodel_found'] for row in rows.values()) == 3


def test_definitions_extend_source_without_new_primitives_or_source_claims():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child, basis = source_composed()
    doc = parse(child)
    assert doc['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert doc['statements'] == parent['statements']
    for builder, counts in ((generic_composed, (0, 7)), (source_composed, (183, 264))):
        text, basis = builder()
        report = audit_basis(parse(text), basis)
        assert (report['primitive_count'], report['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
