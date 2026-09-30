from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_directed_presentations import (
    alignment, conditional_checks, degree_checks, presentation_checks, source_checks, temporal_checks,
)
from scripts.compose_directed_presentations import ROOT, generic_composed, source_composed


def test_presentation_binds_roles_without_evaluating_message_content():
    rows = presentation_checks()
    assert len(rows) == 32
    assert sum(row['presented'] for row in rows) == 1
    assert rows[-1]['presented']


def test_temporal_prerequisite_requires_the_same_distinct_prior_context():
    rows = temporal_checks()
    assert len(rows) == 64
    for row in rows:
        assert row['valid'] == any(row['before'][s] and row['prerequisite'][s] for s in ('first', 'third'))
    assert any(row['before']['now'] and row['prerequisite']['now'] and not row['valid'] for row in rows)


def test_conditional_truth_applicability_actuality_and_message_force_are_separate():
    rows = conditional_checks()
    assert len(rows) == 16
    assert all(row['same_assertion_and_question_content'] and row['different_message_force'] for row in rows)
    assert any(row['conditional'] and not row['applicable'] and not row['actual_danger'] for row in rows)
    assert any(not row['conditional'] and row['actual_danger'] for row in rows)


def test_source_warning_keeps_recipients_fixed_when_checking_prior_prevention():
    rows = source_checks()
    assert len(rows) == 13
    assert [name for name, row in rows.items() if row['after_same_recipients_prevented']] == ['baseline']
    assert all(not row['earlier_context_has_same_selection'] for row in rows.values())
    assert all(not row['communicated_conditional_evaluated'] for row in rows.values())
    assert rows['no_prior_effect']['presentation']
    assert not rows['split_senders']['presentation']
    assert not rows['split_recipients']['presentation']
    assert not rows['wrong_subject']['presentation']
    assert not rows['wrong_message_force']['presentation']


def test_not_so_great_danger_does_not_mean_no_danger():
    rows = degree_checks()
    assert len(rows) == 4
    assert rows['some_danger_not_high']['scoped_claim']
    assert rows['actually_high']['possible_adversity'] and not rows['actually_high']['not_so_great']
    assert not rows['no_danger']['possible_adversity'] and not rows['no_danger']['not_so_great']
    assert rows['empty_audience']['not_so_great'] and not rows['empty_audience']['scoped_claim']


def test_partial_readings_are_not_promoted_to_unconditional_author_claims():
    row = alignment()
    assert len(row['segments']) == 2
    assert all(segment['status'] == 'partial_explicit_reading' for segment in row['segments'])
    assert not row['full_semantic_equivalence']
    assert 'literal walking depiction' in row['remaining']
    prior = parse((ROOT / 'examples/v014/kant-scoped-interventions.noema').read_text(encoding='utf-8'))
    assert parse(source_composed()[0])['statements'] == prior['statements']
    assert len(prior['statements']) == 8


def test_presentation_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 2)), (source_composed, (125, 174))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
