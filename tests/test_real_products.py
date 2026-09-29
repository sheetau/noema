from pathlib import Path

import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_real_products import composed


def test_general_root_candidate_keeps_strict_boundaries():
    text, _ = composed()
    text += '''
q[c[k cj[k bb[n p c b]]][n p h f]].
q[c[k cj[k bb[n p c b]]][n p d c]].
q[c[k cj[k bb[n p e b]]][n p c b]].
q[c[k cj[k bb[n p a b]]][n p a b]].
q[c[k cj[k bb[n p a b]]][n u b h]].
'''
    actual = evaluate_document(parse(text), individuals=('object',), situations=('now',),
                               primitives={'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
                                           'ac': lambda a: -a, 'ad': lambda a, b: a * b})
    assert [r['value'] for r in actual] == [True, False, False, False, True]


def test_no_finite_rational_sampling_is_used_for_products():
    text, _ = composed()
    text += 'q[c[k cc[k bb[n p b b] k bb[n p b b]]][n p b c]].'
    with pytest.raises(ValueError, match='rational number domain'):
        evaluate_document(parse(text), individuals=('object',), situations=('now',),
                          primitives={'aa': lambda a, b: a < b, 'ab': lambda a, b: a + b,
                                      'ac': lambda a: -a, 'ad': lambda a, b: a * b})


def test_products_use_only_existing_rational_operations_and_roundtrip():
    text, basis = composed()
    doc = parse(text)
    audit = audit_basis(doc, basis)
    assert audit['primitive_count'] == 4
    assert audit['definition_count'] == 22
    for notation in ('compact', 'full'):
        canonical = format_graph(doc, notation)
        assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
    assert '<svg' in render(text, alphabet='v2')


def test_polynomial_lemmas_and_source_formula_alignment():
    pytest.importorskip('z3')
    if not Path('artifacts/written-units-v1/einstein-1905.json').exists():
        pytest.skip('Source artifact is prepared separately')
    from scripts.check_real_products import build_report
    report = build_report()
    statuses = [r['status'] for r in report['universal_rational_polynomial_checks'].values()]
    assert statuses.count('valid') == 13
    assert statuses.count('invalid') == 3
    assert report['source_alignment']['math_id'] == 'M0136'
    assert report['source_alignment']['status'] == 'partial'
    assert not report['general_real_field_laws_machine_verified']
    assert not report['cut_beta_and_algebraic_beta_equivalence_machine_verified']
    assert report['verified_full_units'] == 0
