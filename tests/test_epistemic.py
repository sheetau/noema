from pathlib import Path

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import encode, decode
from scripts.compose_epistemic import composed, einstein_composed
from scripts.check_epistemic import awareness_checks, phi_checks, build_report


def test_recognition_truth_and_negative_knowledge_are_separate():
    cases = awareness_checks()
    assert len(cases) == 9
    selective = cases['one_description_only']['actual']
    assert selective['content_equal'] and selective['factive_recognized']
    assert not selective['equivalent_description_recognized']
    false_belief = cases['false_belief_is_not_factive']['actual']
    assert false_belief['recognized_supported'] and not false_belief['factive_recognized']
    absent = cases['true_but_no_recognition']['actual']
    assert absent['positive_not_recognized_as_true'] and not absent['negative_recognized']
    assert cases['settled_false_and_recognized_negative']['actual']['negative_recognized']
    empty = cases['empty_alternatives_are_not_knowledge']['actual']
    assert not empty['all_true'] and not empty['all_false'] and not empty['unsettled']


def test_phi_point_observation_is_not_a_whole_function_comparison():
    cases = phi_checks()
    assert len(cases) == 10
    assert not cases['same_at_three_does_not_identify_function']['actual']
    assert cases['different_at_four']['actual']
    assert cases['actual_phi_two_reaches_four_coordinate_equations']['actual']
    assert not cases['silently_setting_phi_to_one_fails']['actual']
    assert 'refused' in cases['sp_whole_rational_domain_not_sampled']
    assert 'refused' in cases['sr_whole_rational_domain_not_sampled']


def test_documents_keep_primitive_assumptions_visible_and_roundtrip():
    for compose, counts in ((composed, (2, 7)), (einstein_composed, (12, 61))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert not audit['semantic_equivalence_to_source_proven']
        for notation in ('full', 'compact'):
            canonical = format_graph(doc, notation)
            assert parse(canonical) == parse(decode(encode(canonical, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')


def test_original_unknown_function_clause_is_only_a_partial_draft():
    if not Path('artifacts/written-units-v1/einstein-1905.json').exists():
        pytest.skip('Source artifact is prepared separately')
    report = build_report()
    assert report['source_alignment']['status'] == 'partial'
    assert report['source_alignment']['selection']['text'] == 'eine vorläufig unbekannte Funktion von'
    assert report['verified_full_units'] == {'einstein-1905': 0, 'kant-1784': 0}
    assert not report['general_knowledge_theory_complete']
    assert not report['whole_phi_function_machine_verified']
