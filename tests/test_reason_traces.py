from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from scripts.check_reason_traces import CASES, INVALID, FORMULAS, DOMAIN, SCENES, setup, model_for, values
from scripts.compose_reason_traces import ROOT, PARENT, SOURCE, BASIS, build, basis
from scripts.compose_limits import call as k


@pytest.mark.parametrize('name', [*CASES, 'repeat'])
def test_valid_reason_traces_do_not_execute_quoted_claims(name):
    # No interpretations for the quoted propositions are supplied: evaluation
    # would raise. This tests the Noema definition, not a Python proof checker.
    assert values(name) == [True, True, name != 'premise']


@pytest.mark.parametrize('name', INVALID)
def test_invalid_order_circularity_aliases_and_rules_are_rejected(name):
    assert values(name) == [True, False, False]


@pytest.mark.parametrize('name,truths', list(product(CASES, product((False, True), repeat=2))))
def test_each_rule_preserves_truth_when_its_premises_are_true(name, truths):
    result = values(name, truth=True, truths=truths)
    valuation = dict(zip(('p', 'q', 'implication', 'conjunction'), result[-4:]))
    assert result[1]
    assert not all(valuation[p] for p in CASES[name]['premises']) or valuation[CASES[name]['goal']]


def test_valid_conditional_reason_does_not_imply_actual_truth():
    assert values(truth=True, truths=(False, False)) == [True, True, True, False, False, True, False]


def test_known_conclusion_and_using_a_reason_are_separate_conditions():
    # The model assigns the same judgment and conclusion at both stages, and
    # the content is true at both. Only its reason-use relation changes.
    assert values(connection=True, truth=True, truths=(True, True)) == [True, True, True, False, True, True, True, True, True]


def test_conclusion_used_as_a_premise_is_valid_derivation_but_not_independent_support():
    assert values('reused_conclusion', connection=True) == [True, True, True, False, False]


def test_available_but_unused_conclusion_premise_does_not_invalidate_support():
    data = deepcopy(setup(connection=True))
    data['case']['premises'] += ('q',)
    result = evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES, primitives=model_for(data))
    assert [r['value'] for r in result] == [True, True, True, False, True]


@pytest.mark.parametrize('variant', ('wrong_claim', 'wrong_subject', 'wrong_user', 'wrong_reason', 'wrong_context'))
def test_reason_must_support_the_same_judgment_subject_and_context(variant):
    assert values(connection=True, variant=variant) == [True, True, True, False, False]


def test_unknown_premise_adoption_is_not_false_filled():
    with pytest.raises(ValueError, match='Premise adoption is unknown'):
        values(variant='unknown_premise')


def test_equal_truth_profiles_do_not_make_different_descriptions_interchangeable():
    # p and alias have identical interpretations, but the proof supplies an
    # implication with alias while attempting to use p as its antecedent.
    assert values('alias', truth=True, truths=(True, True))[:3] == [True, False, False]


def test_composed_rules_can_form_a_longer_reason():
    data = deepcopy(setup('mp')); row = data['case']
    row.update(steps=('p', 'i', 'q', 'c'), goal='conjunction')
    row['forms']['c'] = 'conjunction'; row['rules']['c'] = 2
    doc = data['document']; original = next(d for d in doc['declarations'] if d['name'] == 'rqu')
    # Change the two query goals to the exact conjunction constructor; retain
    # the same certificate checker and model dispatch.
    queries = parse((ROOT / SOURCE).read_text(encoding='utf-8') +
        'r jap[] e.r jaq[] e.q[e[' + FORMULAS['conjunction'] + '][' + FORMULAS['conjunction'] + ']].')['statements']
    goal = queries[0]['body']['arguments'][0]
    for statement in doc['statements'][1:]:
        statement['body']['arguments'][1] = deepcopy(goal)
    assert original['name'] == 'rqu'
    result = evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model_for(data))
    assert [r['value'] for r in result] == [True, True, True]


def test_verification_rules_and_existing_judgment_definition_are_stored_in_noema():
    text = build(); assert (ROOT / SOURCE).read_text(encoding='utf-8') == text
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    doc = parse(text)
    assert all(d['kind'] == 'definition' for d in doc['declarations'])
    assert not doc['statements']
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][0] == next(d for d in parent['declarations'] if d['name'] == 'ya')
