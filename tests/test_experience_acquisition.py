from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.check_experience_acquisition import (
    acquisition_checks, alignment, attribution_checks, sequence_checks, source_checks,
)
from scripts.compose_experience_acquisition import ROOT, generic_composed, source_composed


def test_experience_order_matches_independent_enumeration_and_scales_linearly():
    result = sequence_checks()
    assert result['enumerated_sequences_and_time_assignments'] == 2560
    assert result['long_sequence_length'] == 24
    assert result['long_sequence_step_budget'] == 5000
    assert 0 < result['accepted'] < 2560


def test_acquisition_requires_assessed_change_and_causal_contribution():
    result = acquisition_checks()
    assert len(result['truth_cases']) == 64
    assert sum(row['acquired'] for row in result['truth_cases']) == 1
    assert len(result['binding_contrasts']) == 8
    assert not any(result['binding_contrasts'].values())


def test_source_forecast_is_neither_present_ability_nor_unassessed_inability():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 20
    assert not result['definitions_replaced_by_primitives']
    assert rows['baseline'] == {'witness': True, 'prospect': True, 'current_ability': False, 'scoped_prospect': True}
    assert not rows['unassessed_before']['witness'] and not rows['unassessed_after']['witness']
    assert not rows['unknown_result']['witness'] and not rows['successful_trial']['witness']
    assert not rows['no_contribution']['witness']
    assert rows['bad_additional_prospect']['witness'] and not rows['bad_additional_prospect']['prospect']
    assert rows['empty_audience']['prospect'] and not rows['empty_audience']['scoped_prospect']


def test_authors_reason_direction_and_content_are_preserved_without_evaluation():
    rows = attribution_checks()
    assert len(rows) == 7
    assert [name for name, row in rows.items() if row['attribution']] == ['baseline']
    assert all(not row['underlying_contents_evaluated'] for row in rows.values())


def test_source_alignment_does_not_certify_literal_metaphor_or_complete_meaning():
    row = alignment()
    assert row['status'] == 'partial_explicit_reading'
    assert not row['full_semantic_equivalence']
    assert row['start'] == 1259 and row['end'] == 1324
    assert 'literal falling and walking' in row['remaining']
    prior = parse((ROOT / 'examples/v014/kant-directed-presentations.noema').read_text(encoding='utf-8'))
    assert parse(source_composed()[0])['statements'] == prior['statements']


def test_acquisition_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 2)), (source_composed, (135, 183))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
