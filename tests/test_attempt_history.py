import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_attempt_history import (
    evidence_checks, independence_checks, scope_checks, ability_checks, explanation_checks, alignment,
)
from scripts.compose_attempt_history import ROOT, PARENT, generic_composed, source_composed


def test_missing_and_conflicting_evidence_do_not_establish_never():
    rows = evidence_checks()
    assert len(rows) == 64
    assert json.loads(json.dumps(rows)) == rows
    missing = next(r for r in rows if r['scope'] == [True, True] and r['positive'] == [False, False] and r['negative'] == [False, False])
    assert missing['results'] == [True, False, False]
    contradictory = next(r for r in rows if r['scope'] == [True, True] and r['positive'] == [True, False] and r['negative'] == [True, True])
    assert contradictory['results'] == [False, False, False]
    assert all(r['results'] == [True, True, True] for r in rows if r['scope'] == [False, False])


def test_permission_attempt_ability_and_causal_explanation_are_independent():
    rows = independence_checks()
    assert len(rows) == 16
    assert sum(r['result'][-1] for r in rows) == 2
    assert any(not r['allowed'] and r['attempted'] and r['able'] for r in rows)


def test_negative_history_keeps_person_activity_time_and_actual_history():
    rows = scope_checks()
    assert len(rows) == 12
    assert rows['different_agent'][0] is False
    assert rows['different_person'][0] and rows['different_activity'][0]
    assert rows['permission_future'][0] and rows['permission_alternative'][0]
    assert not rows['permission_older'][0]
    assert not rows['missing_anchor'][0] and not rows['cyclic_order'][0]


def test_own_understanding_does_not_silently_require_absence_of_guidance():
    rows = ability_checks()
    assert rows['baseline:True'][2:] == [False, False, True]
    assert rows['missing_assessment:True'][2:] == [False, False, False]


def test_explanation_keeps_same_person_descriptions_and_context():
    rows = explanation_checks()
    assert len(rows) == 6
    assert [name for name, result in rows.items() if result[-1]] == ['baseline']
    assert all(result[:3] == [True, True, True] for result in rows.values())


def test_third_paragraph_is_partial_and_does_not_assert_inexperience():
    row = alignment()
    assert row['unit'] == 'kant-1784:u0010'
    assert row['status'] == 'partial_explicit_reading' and not row['full_semantic_equivalence']
    assert row['actual_attempt_absence_not_asserted']
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse(source_composed()[0])
    assert child['statements'] == parent['statements']
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']


def test_basis_and_independent_alphabet_roundtrips():
    for builder, counts in ((generic_composed, (0, 4)), (source_composed, (146, 207))):
        text, basis = builder()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
