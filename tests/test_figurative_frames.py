from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_figurative_frames import (
    attribution_checks, depiction_checks, frame_binding_checks, generic_checks,
)
from scripts.compose_figurative_frames import ROOT, generic_composed, source_composed


def test_framing_does_not_require_literal_truth_or_collapse_equal_contents():
    rows = generic_checks()
    assert len(rows) == 8
    assert all(row['framing_condition'] == row['framed'] for row in rows)
    assert all(not row['identical_description_accepted'] for row in rows)
    contrast = next(row for row in rows if row['framed'] and row['target_true'] and not row['depiction_true'])
    assert contrast['target_and_framing'] and not contrast['equal_contents']


def test_description_bindings_and_depiction_scope_remain_distinct():
    bindings, depictions = frame_binding_checks(), depiction_checks()
    assert len(bindings) == 7 and len(depictions) == 8
    assert [key for key, row in bindings.items() if row['accepted']] == ['baseline']
    assert [key for key, row in depictions.items() if row['depiction_true_in_supplied_interpretation']] == ['baseline']
    assert all(not row['contents_evaluated'] for row in bindings.values())
    assert all(not row['status_evaluated'] for row in depictions.values())


def test_source_annotation_does_not_assert_natural_speech_or_change_old_claims():
    rows = attribution_checks()
    assert rows['framed']['statements'] == [True, True, True]
    assert rows['unframed']['statements'] == [True, True, False]
    assert all(not row['depiction_and_target_evaluated'] for row in rows.values())


def test_figurative_basis_and_written_forms():
    for compose, counts in ((generic_composed, (1, 2)), (source_composed, (69, 95))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
