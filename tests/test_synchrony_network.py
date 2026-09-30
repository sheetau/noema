from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_synchrony_network import (
    adapter_checks, alignment, attribution_checks, relation_checks, scope_checks, trial_checks,
)
from scripts.compose_synchrony_network import ROOT, generic_composed, source_composed


def test_two_relational_laws_do_not_alone_make_all_clocks_synchronous():
    result = relation_checks()
    assert len(result['cases']) == 512
    assert result['joint_law_models'] == 15
    assert result['same_reference_models'] == 64
    assert result['all_three_models'] == 1
    assert result['empty_selection'] == [True, True, False]
    assert not result['arbitrary_size_physical_realizability_proved']


def test_all_relevant_trials_require_a_nonempty_scope_and_every_criterion():
    rows = trial_checks()
    assert len(rows) == 16
    assert any(row['accepted'] for row in rows)
    assert all(not row['accepted'] for row in rows if not any(row['selected']))
    assert not next(row for row in rows if row['selected'] == [True, True] and row['criteria'] == [True, False])['accepted']


def test_clock_scope_does_not_ignore_invalid_selected_clocks():
    rows = scope_checks()
    assert len(rows) == 8
    assert [name for name, accepted in rows.items() if accepted] == ['baseline']


def test_protocol_adapter_preserves_the_same_clock_pair_frame_unit_and_trial():
    result = adapter_checks()
    assert len(result['cases']) == 15
    assert [name for name, row in result['cases'].items() if row['accepted']] == ['baseline']
    assert result['criterion_is_injected_binding_oracle']
    assert not result['full_real_cut_protocol_evaluated']


def test_author_assumption_is_not_executed_as_a_physical_proof():
    rows = attribution_checks()
    assert len(rows) == 6
    assert [name for name, row in rows.items() if row['attributed']] == ['baseline']
    assert all(not row['physical_contents_evaluated'] for row in rows.values())


def test_four_source_fragments_remain_partial():
    report = alignment()
    assert len(report['segments']) == 4 and report['verified_full_units'] == 0
    assert [row['unit'] for row in report['segments']] == [f'einstein-1905:u{i:04d}' for i in range(15, 19)]
    assert all(not row['full_semantic_equivalence'] for row in report['segments'])
    assert report['segments'][-1]['start'] > 0


def test_synchrony_definitions_retain_the_physical_protocol_and_roundtrip():
    for compose, counts in ((generic_composed, (0, 4)), (source_composed, (36, 25))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
    doc = parse(source_composed()[0])
    protocol = parse((ROOT / 'examples/v011/einstein-clock-protocol.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(protocol['declarations'])] == protocol['declarations']
    assert len(doc['statements']) == 1
