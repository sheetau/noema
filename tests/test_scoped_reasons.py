from itertools import product
import json

import pytest

from noema.constructed import parse
from scripts.check_scoped_reasons import CASES, INVALID, OLD_CASES, OLD_INVALID, FORMULAS, values, previous_values, written_example
from scripts.compose_scoped_reasons import ROOT, PARENT, SOURCE, CORE, BASIS, build, basis


@pytest.mark.parametrize('name', CASES)
def test_conditional_reasons_are_checked_without_executing_the_assumptions(name):
    assert values(name) == [True, True, True, name != 'scoped_mp']


@pytest.mark.parametrize('name', INVALID)
def test_no_open_assumption_or_other_scope_can_escape(name):
    assert values(name) == [True, False, False, False]


@pytest.mark.parametrize('name,truths', list(product(CASES, product((False, True), repeat=2))))
def test_every_scoped_step_and_closed_goal_preserves_truth_conditionally(name, truths):
    result = values(name, truth=True, truths=truths)
    valuation = dict(zip(FORMULAS, result[4:]))
    premises = all(valuation[n] for n in CASES[name]['premises'])
    for line in CASES[name]['rows']:
        assert not (premises and all(valuation[n] for n in line['scope'])) or valuation[line['form']]
    assert not premises or valuation[CASES[name]['goal']]


@pytest.mark.parametrize('name', (*OLD_CASES, *OLD_INVALID, 'repeat'))
def test_empty_scope_retains_old_validity_derivation_and_support_checks(name):
    assert previous_values(name) == values('old_' + name)


@pytest.mark.parametrize('variant', ('baseline', 'wrong_claim', 'wrong_subject', 'wrong_user', 'wrong_reason', 'wrong_context'))
def test_discharged_conditional_reason_binds_to_the_same_judgment(variant):
    assert values(connection=True, variant=variant) == [True, True, True, True, False, variant == 'baseline']


@pytest.mark.parametrize('variant,match', [('unknown_scope', 'Hypothesis scope is unknown'), ('unknown_premise', 'Premise adoption is unknown')])
def test_missing_scope_and_premise_interpretations_are_not_silently_completed(variant, match):
    with pytest.raises(ValueError, match=match): values(variant=variant)


def test_false_hypothesis_can_be_discharged_without_becoming_a_fact():
    result = values(truth=True, truths=(False, False))
    valuation = dict(zip(FORMULAS, result[4:]))
    assert result[:4] == [True, True, True, True]
    assert not valuation['p'] and valuation['identity']


def test_identical_truth_profiles_do_not_merge_hypothesis_descriptions():
    result = values('alias_scope', truth=True, truths=(True, True))
    valuation = dict(zip(FORMULAS, result[4:]))
    assert valuation['p'] == valuation['alias']
    assert result[:4] == [True, False, False, False]


def test_assuming_the_goal_locally_is_different_from_adopting_it_as_global_premise():
    assert values('unused_local_goal') == [True, True, True, True]
    assert values('scoped_mp') == [True, True, True, False]


def test_artifacts_preserve_existing_definitions_and_do_not_add_primitive_meanings():
    texts = build(); assert all((ROOT / p).read_text(encoding='utf-8') == t for p, t in texts.items())
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis()
    parent, source, core = [parse((ROOT / p).read_text(encoding='utf-8')) for p in (PARENT, SOURCE, CORE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(source['declarations']) == len(parent['declarations']) + 7
    assert all(d['kind'] == 'definition' for d in core['declarations'])
    assert not source['statements'] and not core['statements']
    names = {d['name'] for d in core['declarations']}
    assert {'rra', 'rrb', 'rrc', 'rrd', 'rre', 'rrf', 'rrg', 'ya', 'rqq', 'rqr', 'rqs'} == names


def test_written_proof_asserts_the_records_without_asserting_the_false_hypothesis():
    assert written_example() == [{'kind':'assert','value':True}] * 7 + [{'kind':'ask','value':x} for x in (True, True, False, True)]


@pytest.mark.parametrize('variant', ('wrong_rule', 'open_scope'))
def test_written_record_mutations_fail_metadata_assertions_and_the_proof_check(variant):
    result = written_example(variant)
    assert not all(row['value'] for row in result[:7])
    assert [row['value'] for row in result[7:]] == [False, False, False, True]
