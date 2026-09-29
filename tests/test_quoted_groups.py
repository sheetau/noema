from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_quoted_groups import generic_checks, source_checks, attribution_check
from scripts.compose_quoted_groups import ROOT, generic_composed, source_composed


def test_quoted_groups_preserve_order_repetition_and_membership():
    result = generic_checks()
    rows = result['ordered_sequences']
    assert len(rows) == 15
    assert [r['parts'] for r in rows if r['whole_role']] == [['za', 'zb']]
    assert next(r for r in rows if r['parts'] == ['za', 'za'])['first_member']
    assert not next(r for r in rows if r['parts'] == ['za', 'za'])['second_member']
    assert result['empty_rejected_even_if_role_primitive_true']
    assert not result['underlying_contents_evaluated']


def test_whole_motto_role_does_not_distribute_to_or_follow_from_parts():
    rows = source_checks()
    assert len(rows) == 9
    assert rows['whole_only']['whole'] and not rows['whole_only']['latin'] and not rows['whole_only']['german']
    assert not rows['both_separate_only']['whole']
    assert rows['both_separate_only']['latin'] and rows['both_separate_only']['german']
    assert rows['whole_and_parts']['whole'] and rows['whole_and_parts']['latin']
    for name in ('reversed_only', 'duplicate_only', 'wrong_topic', 'wrong_context'):
        assert not rows[name]['whole']
    assert all(r['latin_member'] and r['german_member'] for r in rows.values())


def test_grouped_motto_keeps_quotes_and_explanation_edge_unevaluated():
    rows = attribution_check()
    assert len(rows) == 4 and rows['baseline']['actual']
    assert all(not r['actual'] for name, r in rows.items() if name != 'baseline')
    assert all(not r['contents_evaluated'] for r in rows.values())
    assert rows['baseline']['references'][-1] == ['conclusion', 'bo']


def test_quoted_group_basis_and_written_forms():
    for compose, counts in ((generic_composed, (1, 2)), (source_composed, (36, 38))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
