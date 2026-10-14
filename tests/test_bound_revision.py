import json

import pytest

from noema.grammar import parse
from scripts.check_bound_revision import REPORT, build_report
from scripts.compose_bound_revision import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_ordered_binding_preserves_each_position_and_duplicate(result):
    adapter = result['adapter']
    assert adapter['models'] == 64 and adapter['valid_sequences_per_model'] == 32
    assert adapter['invalid_lengths'] == [0, 1, 4, 6]
    assert adapter['independent_positional_oracle'] and adapter['repeated_elements_preserved']
    assert not adapter['general_higher_order_proof']


def test_bound_modal_results_equal_direct_applications(result):
    for row in result['modal']['cases']:
        applicable, left, right = row['bits']
        expected = applicable and left and right
        assert row['results'] == [expected] * 4 + [not applicable or left and right] * 2
    assert result['modal']['contrasts'] == {
        'other_holder': [False] * 6,
        'other_epoch': [False] * 6,
        'other_contract': [False] * 4 + [True] * 2,
    }


def test_full_policy_can_be_aimed_at_without_achieving_its_modal_result(result):
    for row in result['chain']['cases']:
        assert row['result'] == (row['aimed'] and row['solemnity'])
    assert result['chain']['unknown_goal_contents_not_executed']
    assert result['chain']['same_case_for_goal_and_policy']
    assert result['chain']['alternative_readings'] == {'hzdv': True, 'hzdw': True}


def test_changed_group_epoch_agreement_or_binding_is_not_the_same_policy(result):
    assert result['chain']['contrasts'] == {name: False for name in (
        'other_group', 'other_epoch', 'other_contract', 'reversed_aim', 'empty', 'extra')}
    assert result['chain']['closed_roundtrips']
    assert result['chain']['bound_positions'] == [[1], [1]]
    assert all(n > 0 for n in result['chain']['disquotations_removed'])


def test_achieved_goal_requires_the_exact_causal_result_and_joint_act(result):
    assert len(result['achieved']['cases']) == 16
    for row in result['achieved']['cases']:
        assert row['result'] == all(row['bits'])
    assert len(result['achieved']['contrasts']) == 6
    assert not any(result['achieved']['contrasts'].values())
    assert result['achieved']['same_modal_result_executed']
    assert result['achieved']['unknown_relations_refused']


def test_universal_norms_keep_the_complete_policy_without_executing_it(result):
    assert len(result['norms']['cases']) == 16
    for row in result['norms']['cases']:
        f1, f2, p1, p2 = row['bits']
        assert row['results'] == [f1 and f2, not p1 and not p2]
    assert result['norms']['same_full_policy_for_all_contracts']
    assert result['norms']['unknown_contract_formation_and_goal_not_executed']
    assert result['norms']['quoted_policy_not_a_primitive_placeholder']


def test_parent_and_interpretation_limits_are_preserved(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-bound-revision.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 5
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))


def test_two_valid_contracts_select_their_own_terms_and_arguments():
    from scripts.check_bound_revision import assemble, query_policy, policy_model, CHAIN_CASE, bound, values, seq, syntax
    from scripts.check_closed_policies import quoted
    setup = assemble((ROOT / 'examples/v014/bound-revision-core.noema').read_text(encoding='utf-8'))
    doc = query_policy(setup)
    model = policy_model(doc, setup)
    original_invokes = model['jeinvokes']
    terms = {pact: syntax(quoted('function_ref', name)) for pact, name in (('pact', 'jq'), ('other', 'jr'))}
    records = (('alpha', 'acta', 'first'), ('beta', 'actb', 'second'))
    allocation = model['jh']
    model.update(jbpact=lambda pact: pact in terms,
        jballocation=lambda pact, person: allocation(person) if pact == 'pact' else seq((person,)),
        jl=lambda pact, target, context: pact in terms and target.syntax == terms[pact] and context == 'now',
        jo=lambda person, act, pact, target, bindings, scene: (person, act, scene) in records and pact in terms
            and target.syntax == terms[pact] and bindings.items == (allocation(person).items if pact == 'pact' else (person,)),
        jeinvokes=lambda person, act, title, message, bindings, scene: original_invokes(person, act, title, message,
            allocation(person), scene) and bindings.items in (allocation(person).items, (person,)),
        jbaims=lambda person, act, goal, bindings, scene: (person, act, scene) == ('alpha', 'acta', 'first')
            and goal.syntax == syntax(setup['goal']) and bindings.items in (CHAIN_CASE, (*CHAIN_CASE[:-1], 'other')))
    for pact in ('pact', 'other'):
        model['jbcase'] = lambda pact=pact: seq((*CHAIN_CASE[:-1], pact))
        assert values(doc, model, bound.cohorts.DOMAIN, bound.cohorts.SCENES) == [True]
    # The second contract cannot borrow the first contract's clause arguments.
    model['jballocation'] = lambda pact, person: allocation(person)
    assert values(doc, model, bound.cohorts.DOMAIN, bound.cohorts.SCENES) == [False]
