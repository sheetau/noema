import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_asymptotics import attribution_check, finite_checks, witness_checks, scalar_checks, source_alignment
from scripts.compose_asymptotics import ROOT, composed, source_composed


def test_error_scale_sign_and_asymptotic_quantifier_scope():
    assert len(finite_checks()) == 6
    pytest.importorskip('z3')
    rows = witness_checks()
    assert len(rows) == 9
    assert sum(row['status'] == 'valid' for row in rows.values()) == 4
    assert rows['negative_comparison_scale_uses_absolute_value']['status'] == 'valid'
    assert rows['bounded_constant_error_need_not_tend_to_zero']['status'] == 'valid'
    assert rows['empty_domain_is_not_asymptotic']['status'] == 'invalid'
    assert rows['zero_scale_cannot_hide_nonzero_error']['status'] == 'invalid'


def test_remainder_bounds_reuse_the_existing_exact_clock_lemmas():
    pytest.importorskip('z3')
    rows = scalar_checks()
    assert len(rows) == 5 and all(row['status'] == 'valid' for row in rows.values())
    assert rows['duration_scales_the_same_remainder']['status'] == 'valid'


def test_approximation_changes_only_the_scoped_consequent():
    doc = parse(source_composed()[0])
    definitions = {d['name']: d for d in doc['declarations']}
    matrices = []
    for name in ('qd', 'qf'):
        node = definitions[name]['body']['body']
        while node['kind'] == 'forall':
            node = node['body']
        assert node['kind'] == 'implies'
        matrices.append(node)
    assert matrices[0]['arguments'][0] == matrices[1]['arguments'][0]
    assert matrices[1]['arguments'][1]['kind'] == 'exists'
    assert attribution_check() == {'quoted_assumption': 'qc', 'quoted_conclusion': 'qf', 'contents_evaluated': False}


def test_basis_roundtrip_and_approximation_source_qualification():
    for compose, counts in ((composed, (4, 47)), (source_composed, (24, 73))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
    alignment = source_alignment()
    assert [row['math_id'] for row in alignment['selections']] == ['M0229', 'M0241']
    assert alignment['duration_held_fixed_in_asymptotic_bound']
    assert not alignment['fourth_order_bounds_are_authors_explicit_constants']
