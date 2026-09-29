from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_persistence import order_checks, state_attitude_checks, source_checks, source_alignment, quotation_check
from scripts.compose_persistence import ROOT, generic_composed, source_composed


def test_temporal_scope_requires_order_and_includes_intermediate_points():
    result = order_checks()
    assert result['relations_checked'] == 64 and result['strict_total_orders'] == 6
    assert result['intervals'] == {'000': False, '001': True, '010': True, '011': True,
        '100': True, '101': False, '110': True, '111': True}
    assert result['empty_history_rejected'] and result['outside_history_rejected'] and result['reflexive_order_rejected']


def test_persistence_and_positive_attitude_are_independent_and_nonvacuous():
    result = state_attitude_checks()
    rows = result['cases']
    assert len(rows) == 64 and result['empty_scope_rejected']
    assert sum(row['persistent'] for row in rows) == 8
    assert sum(row['favored_throughout'] for row in rows) == 8
    assert sum(row['persistent'] and row['favored_throughout'] for row in rows) == 1
    gap = next(row for row in rows if row['state'] == [True, False, True] and all(row['favor']))
    assert not gap['persistent'] and gap['favored_throughout']


def test_source_population_binds_the_same_person_state_attitude_and_time():
    result = source_checks()
    assert len(result['cases']) == 12
    assert [name for name, value in result['cases'].items() if value] == ['baseline']
    assert result['attitude_target'] == 'bf'
    assert 'rational number domain' in result['unbounded_ratio_refusal']
    alignment = source_alignment()
    assert len(alignment['fragments']) == 2
    assert alignment['lifetime_scope_and_granularity_are_interpretive_assumptions']
    assert not alignment['positive_attitude_implies_free_choice']
    assert not quotation_check()['content_evaluated']


def test_persistence_basis_and_written_forms():
    for compose, counts in ((generic_composed, (0, 4)), (source_composed, (46, 55))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
