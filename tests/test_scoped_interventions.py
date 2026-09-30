import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.render import render
from noema.script import decode, encode
from scripts.check_scoped_interventions import (
    alignment, contrast_checks, exhaustive_checks, population_checks, scope_checks, source_checks,
)
from scripts.compose_scoped_interventions import ROOT, generic_composed, source_composed


def test_all_two_variable_models_match_independent_solution_enumeration():
    result = exhaustive_checks()
    assert result['binary_models'] == 256 and result['intervention_cases'] == 1024
    assert result['both_target_truth_values_and_guarantee_match'] and result['prevention_matches']


def test_assignment_count_depends_on_variables_not_number_of_individuals():
    rows = scope_checks()
    assert rows['two_variables']['individuals'] == 16
    assert rows['two_variables']['assignments'] == 4
    assert rows['three_variables']['assignments'] == 8
    assert rows['empty']['assignments'] == 1
    assert rows['legacy_large_domain']['refused']
    assert not rows['duplicate']['results'][0] and not rows['nonadjacent_duplicate']['results'][0]
    assert not rows['outside_true']['results'][2]
    assert json.loads(json.dumps(rows)) == rows


def test_prevention_requires_counterfactual_difference_and_nonempty_on_solutions():
    rows = contrast_checks()
    assert [name for name, row in rows.items() if row[-1]] == ['prevents']
    assert rows['never'][:2] == rows['prevents'][:2]
    assert rows['multiple'][:2] == [True, True]
    assert rows['no_solution'] == [False]*4


def test_factual_prevention_requires_bound_activity_consistent_observation_and_model():
    result = source_checks()
    rows = result['cases']
    assert len(rows) == 14
    assert [name for name, row in rows.items() if row['factual_prevention']] == ['baseline']
    assert rows['spontaneous_nonattempt']['actual_restriction']
    assert not rows['spontaneous_nonattempt']['model_prevention']
    assert rows['inconsistent_observation']['model_prevention']
    assert rows['inconsistent_observation']['actual_restriction']
    assert not rows['inconsistent_observation']['factual_prevention']
    assert result['ordinary_baseline_agrees'] and not result['definitions_replaced_by_primitives']


def test_same_previously_selected_population_is_used_without_vacuous_success():
    rows = population_checks()
    assert rows == {'all_targets': True, 'unaffected_target': False,
                    'unrestricted_target': False, 'empty_scope': False}


def test_model_relative_reading_is_not_added_as_an_author_claim():
    row = alignment()
    assert row['segments'][0]['status'] == 'explicit_interpretive_annotation'
    assert not row['full_semantic_equivalence']
    assert 'permission opportunity and courage' in row['remaining']
    prior = parse((ROOT / 'examples/v014/kant-scoped-groups.noema').read_text(encoding='utf-8'))
    assert parse(source_composed()[0])['statements'] == prior['statements']


def test_scoped_intervention_basis_and_original_alphabet_roundtrip():
    for compose, counts in ((generic_composed, (0, 7)), (source_composed, (122, 164))):
        text, basis = compose()
        doc = parse(text)
        audit = audit_basis(doc, basis)
        assert (audit['primitive_count'], audit['definition_count']) == counts
        assert (ROOT / basis['document']).read_text(encoding='utf-8') == text
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            assert parse(form) == parse(decode(encode(form, 'v2'))) == doc
        assert '<svg' in render(text, alphabet='v2')
