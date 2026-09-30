from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_confinement_onset import (
    alignment, attribution_checks, generic_checks, paragraph_review, persistence_checks, source_checks,
)
from scripts.compose_confinement_onset import ROOT, generic_composed, source_composed


def test_onset_requires_assessed_change_and_the_same_applying_process():
    rows = generic_checks()
    assert len(rows) == 256
    assert sum(row['onset'] for row in rows) == 1
    accepted = next(row for row in rows if row['onset'])
    assert not accepted['prior'] and accepted['after'] and all(accepted['assessed'])


def test_initial_inside_position_is_allowed_but_missing_prior_evidence_is_not():
    rows = source_checks()
    assert len(rows) == 18
    assert [name for name, row in rows.items() if row['onset']] == ['baseline', 'outside_before']
    assert all(row['current_state'] for row in rows.values())
    assert all(not row['current_applying_act_condition'] for row in rows.values())


def test_post_onset_persistence_cannot_skip_release_or_unknown_middle_state():
    rows = persistence_checks()
    assert len(rows) == 7
    assert [name for name, row in rows.items() if row['onset_and_persistence']] == ['baseline', 'outside_before']
    assert rows['released_middle']['current_state']
    assert rows['unassessed_middle']['current_state']
    assert not rows['released_now']['current_state']


def test_onset_depiction_is_referenced_without_asserting_its_content():
    rows = attribution_checks()
    assert len(rows) == 3
    assert [name for name, row in rows.items() if row['framed']] == ['baseline']
    assert all(not row['contents_evaluated'] for row in rows.values())


def test_temporal_candidate_does_not_close_source_meaning_review():
    review = paragraph_review()
    assert not review['semantic_completion'] and review['not_a_complete_obligation_inventory']
    assert all(row['status'] == 'open' for row in review['current_obligations'])
    assert not alignment()['full_semantic_equivalence']
    assert parse(source_composed()[0])['statements'] == parse(
        (ROOT / 'examples/v014/kant-training-frame.noema').read_text(encoding='utf-8'))['statements']


def test_onset_basis_and_independent_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 7)), (source_composed, (176, 224))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
