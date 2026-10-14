import json

import pytest

from noema.grammar import parse
from scripts.check_self_legislation import REPORT, build_report, setup, model_for, values, DOMAIN, SCENES
from scripts.compose_self_legislation import ROOT, PARENT


@pytest.fixture(scope='module')
def result(): return build_report()


def test_joint_changes_power_permission_and_question_are_separate(result):
    for section in ('generic', 'source'):
        assert len(result[section]['cases']) == 64
        for row in result[section]['cases']:
            first, second, control, recognition, permit, forbid = row['bits']
            package = first and second
            power = package and control and recognition
            possible = power and permit and not forbid
            assert row['results'] == [package, power, False, possible, possible, possible, possible, False]


def test_clauses_need_one_shared_transition_and_nonempty_package(result):
    for section in ('generic', 'source'):
        assert result[section]['contrasts']['split_endpoints'] == [False] * 8
        assert result[section]['contrasts']['empty_clauses'] == [False] * 8
        assert result[section]['same_transition_for_all_clauses']


def test_permission_and_power_in_different_candidates_do_not_combine(result):
    for section in ('generic', 'source'):
        assert result[section]['contrasts']['split_permission'] == [True, True, False, False, False, False, False, False]
        assert result[section]['contrasts']['split_control'] == [True, False, False, False, False, False, False, False]
        assert result[section]['same_candidate_for_permission_and_power']


def test_self_means_the_same_people_as_actor_and_norm_addressee(result):
    for section in ('generic', 'source'):
        for name in ('other_people', 'other_law'):
            assert result[section]['contrasts'][name] == [False] * 8
        for name in ('other_actor', 'other_exercise', 'wrong_bindings', 'invalid_exercise'):
            assert result[section]['contrasts'][name] == [True, False, False, False, False, False, False, False]


def test_hypothetical_condition_does_not_require_current_permission_or_execution(result):
    for section in ('generic', 'source'):
        row = next(r for r in result[section]['cases'] if r['bits'] == [True, True, True, True, True, False])
        assert row['results'][2:4] == [False, True]
        assert result[section]['actual_permission_or_enactment_not_required']
        assert result[section]['exercise_contents_not_executed']
        assert result[section]['unknown_relations_refused']


def test_necessary_condition_is_not_sufficient_condition(result):
    for section in ('generic', 'source'):
        for row in result[section]['criteria']:
            assert row['results'] == [not row['admissible'] or row['possible'], row['admissible'] == row['possible']]


def test_all_eligible_laws_must_pass_the_same_criterion():
    doc, _ = setup((ROOT / 'examples/v014/self-legislation-core.noema').read_text(encoding='utf-8'), True)
    model = model_for(doc)
    model['jseligible'] = lambda actor, people, law, context: (actor, people, context) == ('monarch', 'people', 'now') and law in ('law', 'otherlaw')
    assert values(doc, model, DOMAIN, SCENES)[4:6] == [True, True]
    model['jsadmissible'] = model['jseligible']
    assert values(doc, model, DOMAIN, SCENES)[4:6] == [False, False]


def test_presenting_the_question_does_not_supply_its_answer(result):
    assert result['question']['cases'] == {'baseline': True, 'other_author': False, 'other_node': False, 'other_context': False, 'assertion_instead': False}
    assert result['question']['unknown_norms_and_candidates_not_executed']
    assert result['question']['no_answer_asserted']


def test_parent_and_partial_source_status_remain_explicit(result):
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-self-legislation.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 14
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
    assert result == json.loads(REPORT.read_text(encoding='utf-8'))
