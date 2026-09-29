from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_proportions import finite_counts, counterexamples, source_checks, source_alignment
from scripts.compose_proportions import ROOT, generic_composed, source_composed


def test_counts_require_nonempty_populations_and_exact_ratios():
    result = finite_counts()
    assert len(result['cases']) == 45
    empty = result['cases'][0]
    assert empty['population_size'] == 0 and not empty['exact_proportion']
    assert all(r['exact_proportion'] for r in result['cases'][1:])
    assert result['larger_population'] == {'size': 64, 'selected': 32, 'exact_ratio': '1/2'}


def test_proportions_reject_bad_counts_and_separate_context_from_majority():
    rows = counterexamples()
    assert len(rows) == 12
    assert not rows['duplicate_person']['unique']
    for name in ('duplicate_person', 'wrong_ratio', 'negative_ratio', 'ratio_above_one',
                 'bad_indicator_double', 'bad_indicator_always_one', 'bad_indicator_always_zero'):
        assert not rows[name]['exact_ratio']
    for name in ('bad_indicator_double', 'bad_indicator_always_one', 'bad_indicator_always_zero'):
        assert not rows[name]['indicator_valid']
    assert rows['outsider_in_domain']['exact_ratio'] and not rows['outsider_in_domain']['contextual_large']
    assert rows['below_half_can_meet_contextual_standard']['contextual_large']
    assert not rows['below_half_can_meet_contextual_standard']['majority']
    assert rows['majority_can_fail_contextual_standard']['majority']
    assert not rows['majority_can_fail_contextual_standard']['contextual_large']
    assert rows['reordered_population']['contextual_large']
    assert rows['same_ratio_larger_population']['contextual_large']


def test_source_share_keeps_population_context_and_unbounded_ratio_explicit():
    result = source_checks()
    assert len(result['cases']) == 7
    assert {name for name, value in result['cases'].items() if value} == {'baseline', 'below_half_contextual'}
    assert 'rational number domain' in result['unbounded_ratio_refusal']
    alignment = source_alignment()
    assert alignment['source'] == 'ein so großer Theil der Menschen'
    assert not alignment['full_predicate_connected']
    assert not alignment['numerical_ratio_or_threshold_asserted']
    assert alignment['population_completeness_is_explicit_assumption']


def test_proportion_basis_and_written_forms():
    for compose, counts in ((generic_composed, (4, 8)), (source_composed, (42, 48))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
