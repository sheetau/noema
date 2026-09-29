import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_described_explanations import generic_checks, source_checks, legacy_collapse_check, attribution_check
from scripts.compose_described_explanations import ROOT, generic_composed, source_composed


def test_causal_adoption_is_not_cooccurrence_or_equal_truth_profiles():
    rows = generic_checks()
    assert len(rows) == 16
    assert all(r['same_property_values'] and r['different_descriptions'] for r in rows)
    assert any(r['cooccurrence'] and not r['adoption'] for r in rows)
    assert any(r['adoption'] and not r['cooccurrence'] for r in rows)
    assert any(r['contrast'] and not r['factor_true'] and not r['effect_true'] for r in rows)
    assert not any(r['contrast'] for r in rows if r['excluded_adopted'])


def test_source_distinguishes_factors_that_the_old_content_relation_collapsed():
    old = legacy_collapse_check()
    assert len(old) == 2
    assert all(r['identical_argument_tuples'] and not r['contrast'] for r in old)
    rows = source_checks()
    assert len(rows) == 11
    assert rows['selected_only']['classification_under_adopted_explanation']
    assert rows['selected_only']['same_factor_content_values']
    for name in ('excluded_only', 'both_adopted', 'neither_adopted', 'wrong_factor_subject',
                 'wrong_effect_subject', 'wrong_effect_description', 'wrong_context', 'reversed_explanation', 'not_a_person'):
        assert not rows[name]['classification_under_adopted_explanation']


def test_source_attribution_does_not_evaluate_explanation_contents():
    result = attribution_check()
    assert result['references'][2] == ['third', 'bp']
    assert len(result['references']) == 6
    assert not result['contents_evaluated']
    text = generic_composed()[0]
    parse(text + 'q[e[r[p ed]][r[p ed]]].')
    with pytest.raises(ValueError, match='disquote-free'):
        parse(text + 'q[e[r[p ec]][r[p ec]]].')


def test_described_explanations_preserve_written_forms_and_basis():
    for compose, counts in ((generic_composed, (1, 3)), (source_composed, (30, 33))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
