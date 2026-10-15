from copy import deepcopy
import json
import pytest
from noema.constructed import parse, format_graph
from scripts.check_political_consequence import values, source_values, attribution, document, alignment
from scripts.compose_political_consequence import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis
from scripts.check_thinking_disposition import code_is


@pytest.mark.parametrize('table', range(16))
def test_all_two_person_structural_outcome_tables(table):
    assert values(table) == [table in (8, 10, 12, 14)]


@pytest.mark.parametrize('variant', ('empty', 'duplicate', 'omitted', 'same_factor', 'undeclared',
    'ambiguous', 'no_off_solution', 'unreviewed_off', 'wrong_premise'))
def test_invalid_coalition_unassessed_world_and_nonunique_outcome_reject_dependency(variant):
    assert values(variant=variant) == [False]


@pytest.mark.parametrize('variant', ('unknown_equation', 'unknown_off'))
def test_unknown_causal_input_is_not_a_negative_outcome(variant):
    with pytest.raises(ValueError, match='Unknown'): values(variant=variant)


def test_original_and_both_intervention_sides_evaluate_real_principle_replacement():
    calls = []
    assert source_values(calls=calls) == [True, True, True]
    probes = [r for r in calls if r[0] == 'normpoint']
    assert any(r[4][:2] == (False, False) for r in probes)
    assert any(r[4][:2] == (True, True) for r in probes)
    norms = [r for r in calls if r[0] == 'norm']
    assert norms and all(r[1:4] == ('norm', 'government', 'office') and r[5:7] == ((), True) for r in norms)
    assert {r[-1] for r in norms} == {'normbase', 'normchanged', 'normkept'}


def test_later_change_alone_is_insufficient_when_it_occurs_without_any_contributor():
    assert source_values(15) == [False, True, True]
    assert source_values(15, indices=(3,)) == [False]


@pytest.mark.parametrize('table', (10, 12, 14))
def test_political_joint_dependency_does_not_claim_each_person_is_necessary(table):
    assert source_values(table, indices=(0,)) == [True]


@pytest.mark.parametrize('variant', ('early', 'simultaneous', 'missing_later_point'))
def test_political_end_must_be_after_cohort_end_in_the_same_history(variant):
    assert source_values(variant=variant, indices=(0, 1)) == [False, False]


@pytest.mark.parametrize('variant', ('unreviewed_off', 'unreviewed_new_off', 'wrong_government', 'old_retained'))
def test_off_side_is_assessed_and_norms_belong_to_the_same_government(variant):
    assert source_values(variant=variant, indices=(0,)) == [False]


@pytest.mark.parametrize('variant', ('unknown_last', 'unknown_off_review', 'unknown_off_norm', 'unknown_policy_equation'))
def test_unknown_political_inputs_remain_unknown(variant):
    with pytest.raises(ValueError, match='Unknown'): source_values(variant=variant, indices=(0,))


def test_full_conditional_keeps_reading_coalition_and_all_three_times():
    calls = []
    assert source_values(indices=(3, 4), calls=calls) == [True, True]
    rest = [r for r in calls if r[0] == 'remaining']
    assert rest and all(r[2:] == ('community', ('person', 'other'), 'end', 'end', 'after', 'political') for r in rest)
    for name in ('iahinner', 'iahvocation'):
        assert any(code_is(r[1], name, 1) for r in rest)
    assert source_values(indices=(6,)) == [False]


def test_false_antecedents_do_not_assert_political_events_but_true_ones_require_remainder():
    assert source_values(all_false=True, variant='unknown_policy_equation', indices=(3,)) == [True]
    assert source_values(remaining=False, indices=(3,)) == [False]
    with pytest.raises(ValueError, match='Unknown dignity'): source_values(variant='unknown_remaining', indices=(3,))


def test_extended_history_and_policy_variable_preserve_actual_cohort_mediation():
    assert source_values(indices=(5,)) == [True]


def test_ranked_attribution_does_not_execute_political_content():
    for path in (CORE, SOURCE):
        assert attribution(path) == [True]
        for variant in ('node', 'author', 'scope', 'context'): assert attribution(path, variant) == [False]
    doc = deepcopy(document(CORE))
    row = next(d for d in doc['declarations'] if d['name'] == 'iasattribution')
    assert row['body']['arguments'][2]['rank'] == 2
    row['body']['arguments'][2]['rank'] = 1
    with pytest.raises(ValueError): parse(format_graph(doc, 'compact'))


def test_parent_preservation_reproducible_artifacts_and_no_false_completion_claim():
    old, new = document(PARENT), document(SOURCE)
    assert new['declarations'][:len(old['declarations'])] == old['declarations']
    assert new['statements'][:-1] == old['statements'][:-1]
    assert values(memoize=False) == values()
    assert all((ROOT / path).read_text(encoding='utf-8') == text for path, text in build().items())
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    assert not alignment()['adds_new_text_coverage'] and not alignment()['semantic_completion']
