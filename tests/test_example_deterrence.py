from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.check_example_deterrence import (
    alignment, attribution_checks, future_scope_checks, scope_checks, source_checks, usual_checks,
)
from scripts.compose_example_deterrence import ROOT, generic_composed, source_composed


def test_all_attempts_requires_nonempty_scope_and_every_selected_item():
    rows = scope_checks()
    assert len(rows) == 16
    assert all(not row['all'] for row in rows if not any(row['selected']))
    assert any(row['all'] and not all(row['holds']) for row in rows)
    assert all(not row['all'] for row in rows if row['selected'] == [True, True] and not all(row['holds']))


def test_usual_allows_exceptions_but_rejects_minorities_and_invalid_denominators():
    report = usual_checks()
    assert report['enumerated_cases'] == 126
    assert report['accepted_with_exceptions'] == 27
    assert len(report['invalid']) == 5
    assert not any(report['invalid'].values())


def test_source_distinguishes_fear_avoidance_explanation_and_population_coverage():
    rows = source_checks()
    assert len(rows) == 21
    assert [name for name, row in rows.items() if row['scoped_usual_claim']] == ['baseline', 'reordered_cases']
    assert rows['reordered_cases'] == rows['baseline']
    assert rows['duplicate_cases']['deterrence_fraction'] == '3/4'
    assert rows['baseline']['deterrence_fraction'] == '2/3'
    assert rows['omit_exception']['deterrence_fraction'] == '1'
    assert rows['mere_nonexecution']['fear_with_example'] and not rows['mere_nonexecution']['deterrence_with_example']
    assert rows['courage_present']['deterrence_with_example'] and not rows['courage_present']['fear_with_example']
    assert rows['no_fear_explanation']['deterrence_with_example'] and not rows['no_fear_explanation']['fear_with_example']
    assert rows['nonhuman_observer']['deterrence_with_example']
    assert rows['one_attempt_not_avoided']['deterrence_fraction'] == '1/3'
    assert all(row['fraction_matches_independent_count'] for row in rows.values())


def test_further_attempts_exclude_past_present_and_different_tasks():
    assert future_scope_checks() == {'futureone': True, 'futuretwo': True, 'pastact': False,
                                     'nowact': False, 'unrelated': False}


def test_attribution_keeps_author_content_and_order_without_evaluation():
    rows = attribution_checks()
    assert len(rows) == 5
    assert [name for name, row in rows.items() if row['attribution']] == ['baseline']
    assert all(not row['contents_evaluated'] for row in rows.values())


def test_partial_generic_reading_does_not_claim_full_paragraph_equivalence():
    row = alignment()
    assert row['status'] == 'partial_explicit_reading' and not row['full_semantic_equivalence']
    assert row['start'] == 1326 and row['end'] == 1438
    assert 'concession and focus' in row['remaining']
    prior = parse((ROOT / 'examples/v014/kant-experience-acquisition.noema').read_text(encoding='utf-8'))
    assert parse(source_composed()[0])['statements'] == prior['statements']


def test_deterrence_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (5, 13)), (source_composed, (144, 194))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
