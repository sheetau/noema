from noema.grammar import parse
from noema.meaning_basis import audit_basis
from scripts.check_unending_persistence import (
    finite_order_checks, finite_tail_checks, general_laws, numerical_witnesses, source_checks, horizon_refusal,
)
from scripts.compose_unending_persistence import ROOT, PARENT, generic_composed, source_composed, witnesses_composed


def test_no_finite_strict_order_or_cyclic_relation_supplies_an_unending_history():
    rows = finite_order_checks()
    assert sum(row['relations'] for row in rows.values()) == 530
    assert [rows[str(size)]['strict_linear_orders'] for size in (1, 2, 3)] == [1, 2, 6]
    assert all(row['unending_models'] == 0 for row in rows.values())


def test_tail_checks_every_later_state_and_includes_the_anchor():
    report = finite_tail_checks()
    assert len(report['cases']) == 24
    assert any(row['states'] == (False, True, True) and row['anchor'] == 1 and row['result'][1] for row in report['cases'])
    assert any(row['states'] == (True, True, False) and row['anchor'] == 0 and not row['result'][1] for row in report['cases'])
    assert report['empty_history_and_missing_anchor_refused']


def test_general_laws_do_not_depend_on_a_finite_sample_of_situations():
    report = general_laws()
    rows = report['claims']
    assert sum(row['status'] == 'valid' for row in rows.values()) == 6
    assert sum(row['countermodel_found'] for row in rows.values()) == 2
    assert rows['persistence_implies_unending']['status'] == 'invalid'
    assert rows['a_last_point_blocks_unending']['status'] == 'valid'


def test_no_final_point_is_strictly_weaker_than_numeric_unboundedness():
    report = numerical_witnesses()
    assert len(report['claims']) == 4
    assert all(row['status'] == 'valid' for row in report['claims'].values())
    assert report['situations_not_retyped_as_numbers']


def test_selected_interval_does_not_entail_remaining_history_or_unending_life():
    rows = source_checks()
    assert len(rows) == 6
    assert rows['only_selected_interval'] == [True, False, False]
    assert rows['all_future'] == [True, True, False]
    assert all(not row[-1] for row in rows.values())


def test_all_rational_horizons_are_not_replaced_by_a_finite_list():
    assert horizon_refusal()['refused']


def test_no_new_kant_claim_or_primitive_is_added():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    for builder, counts in ((generic_composed, (0, 9)), (source_composed, (194, 290)), (witnesses_composed, (1, 4))):
        text, basis = builder()
        audit = audit_basis(parse(text), basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
    source = parse(source_composed()[0])
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'] == parent['statements']
