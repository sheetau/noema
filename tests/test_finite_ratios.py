import pytest

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_finite_ratios import arithmetic_proofs, finite_checks, source_checks
from scripts.compose_finite_ratios import ROOT, generic_composed, source_composed


def test_ratio_uniqueness_and_range_follow_from_guarded_rational_arithmetic():
    pytest.importorskip('z3')
    rows = arithmetic_proofs()
    assert len(rows) == 3 and all(row['status'] == 'valid' for row in rows.values())


def test_computed_ratio_does_not_accept_empty_duplicate_or_invalid_populations():
    result = finite_checks()
    assert len(result['cases']) == 45
    assert result['contrasts']['empty'] == [True, False, False]
    assert result['contrasts']['duplicate'] == [True, False, False]
    assert result['contrasts']['outsider'] == [True, True, False]
    assert result['contrasts']['bad_quotient'] == [False, False, False]
    assert result['contrasts']['bad_indicator'] == [False, False, False]


def test_both_source_results_execute_real_definitions_and_react_independently():
    result = source_checks()
    assert result['cases'] == {'baseline': {'first_result': True, 'second_result': True},
        'high_role_burden': {'first_result': True, 'second_result': False}}
    assert not result['semantic_definitions_stubbed'] and result['pure_definition_memoization']
    assert 'rational number domain' in result['legacy_refusal']


def test_computed_ratio_basis_and_written_forms():
    for compose, counts in ((generic_composed, (5, 11)), (source_composed, (66, 91))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
