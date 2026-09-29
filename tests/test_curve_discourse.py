from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_curve_discourse import source_checks, source_alignment, truth_separation_checks
from scripts.compose_curve_discourse import ROOT, composed, generic_composed, ALIASES


def test_assumption_scope_and_source_attribution_do_not_evaluate_clock_laws():
    rows = source_checks()
    assert len(rows) == 14
    assert rows['baseline']['actual']
    assert all(not row['actual'] for label, row in rows.items() if label != 'baseline')
    assert all(not row['underlying_contents_evaluated'] for row in rows.values())
    assert not rows['wrong_claim_scope']['actual']
    assert not rows['wrong_inference_premise']['actual']


def test_false_content_and_invalid_implication_can_still_be_attributed():
    rows = truth_separation_checks()
    assert len(rows) == 4 and all(row['attributed'] for row in rows.values())
    assert not rows['True_False']['material_implication_truth']
    assert not rows['False_False']['premise_truth'] and not rows['False_False']['result_truth']


def test_observation_premises_do_not_already_impose_the_integral_law():
    doc = parse(composed()[0])
    definitions = {d['name']: d for d in doc['declarations'] if d['kind'] == 'definition'}
    def symbols(node):
        if isinstance(node, list):
            return set().union(*(symbols(item) for item in node))
        if not isinstance(node, dict):
            return set()
        own = {node['symbol']} if node.get('kind') in ('call', 'function_ref') else set()
        return own | set().union(*(symbols(value) for value in node.values()))
    def reachable(name):
        direct = symbols(definitions[name]['body'])
        return direct | set().union(*(reachable(s) for s in direct if s in definitions))
    assert 'ne' not in reachable('qb')
    assert 'ne' in reachable('qc')
    assert 'tb' in reachable('qb')  # Actual endpoint reading relation is retained.
    assert 'lh' in reachable('qb')  # The geometric closed-curve requirement is retained.


def test_basis_roundtrip_and_source_coverage_remain_explicit():
    for compose, counts in ((composed, (24, 62)), (generic_composed, (9, 4))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    basis = composed()[1]
    for previous, alias in ALIASES.items():
        assert next(row for row in basis['primitives'] if row['symbol'] == alias)['source_symbol'] == previous
    alignment = source_alignment()
    assert [row['status'] for row in alignment['segments']] == ['partial', 'partial', 'unwritten']
    assert not alignment['exact_model_equation_is_source_approximation']
