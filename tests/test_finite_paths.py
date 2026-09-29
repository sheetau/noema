from pathlib import Path

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_finite_paths import checks, source_alignment
from scripts.compose_finite_paths import ROOT, composed


def test_path_order_and_accounting_are_independent():
    cases = checks()
    assert len(cases) == 69
    assert cases['triangle_closed_and_lost_two']['actual']
    assert cases['repeated_segments_are_counted_twice']['actual']
    assert cases['swapping_edges_preserves_sum']['actual']
    assert not cases['swapping_edges_breaks_connection']['actual']
    assert cases['different_rates_are_integrated_per_segment']['actual']
    assert not cases['first_rate_cannot_replace_all_rates']['actual']
    assert not cases['closed_empty_path_is_not_a_trip']['actual']
    assert not cases['approximation_is_not_exact']['actual']


def test_general_order_example_needs_no_physical_or_arithmetic_primitive():
    doc = parse((ROOT / 'examples/v014/procedure-order.noema').read_text(encoding='utf-8'))
    results = evaluate_document(doc, individuals=('one',), situations=('now',), primitives={})
    assert len(results) == 4 and all(row['value'] for row in results)


def test_paths_extend_existing_definitions_without_new_primitives():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert (audit['primitive_count'], audit['definition_count']) == (15, 103)
    assert not audit['semantic_equivalence_to_source_proven']
    assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    for notation in ('full', 'compact'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')
    if Path('artifacts/written-units-v1/einstein-1905.json').exists():
        assert len(source_alignment()) == 3
        assert all(row['status'] == 'partial' for row in source_alignment())
