import hashlib
import json

from noema.finite_semantics import Content, FunctionValue
from noema.grammar import parse
from scripts.check_community_protection import (REPORT, setup, model_for, values, DOMAIN, SCENES,
    PROTECT, HARMFUL, STATE_SORT, table_from_corners)
from scripts.compose_community_protection import ROOT, PARENT


def core(): return (ROOT / 'examples/v014/community-protection-core.noema').read_text(encoding='utf-8')


def test_restoring_one_threatened_case_cannot_hide_damage_without_the_threat():
    doc = setup(core(), 'effect')
    # Protection helps when the threat is present but destroys the unthreatened case.
    table = table_from_corners((True, False, False, True))
    assert values(doc, model_for(doc, table=table), DOMAIN, SCENES) == [False, False]


def test_an_ineffective_policy_is_not_protection_even_when_it_does_no_harm():
    doc = setup(core(), 'effect')
    table = table_from_corners((True, False, True, False))
    assert values(doc, model_for(doc, table=table), DOMAIN, SCENES) == [False, True]


def test_communities_can_have_different_activities_under_one_policy():
    doc = setup(core(), 'source'); model = model_for(doc)
    laws, goals, activities = (model[n] for n in ('jvlaws', 'jvgoals', 'jvactivities'))
    model['jvlaws'] = lambda community: FunctionValue(('individual', STATE_SORT), 'truth', lambda variable, state: False) if community == 'beta' else laws(community)
    model['jvgoals'] = lambda community: FunctionValue((STATE_SORT,), 'truth', lambda state: not state('s')) if community == 'beta' else goals(community)
    model['jvactivities'] = lambda community: Content(SCENES, tuple(point.startswith('w') and point[3] == '0' for point in SCENES)) if community == 'beta' else activities(community)
    assert values(doc, model, DOMAIN, SCENES) == [True]
    model['jvactivities'] = activities
    assert values(doc, model, DOMAIN, SCENES) == [False]


def test_not_choosing_reform_does_not_automatically_mean_wanting_the_old_order():
    doc = setup(core(), 'source'); model = model_for(doc, protects=False, harmless=False)
    model['jvchangeconditions'] = lambda community: Content(SCENES, (False,) * len(SCENES))
    model['jvstayconditions'] = lambda community: Content(SCENES, (False,) * len(SCENES))
    assert values(doc, model, DOMAIN, SCENES) == [True]
    model['jvstayconditions'] = lambda community: Content(SCENES, tuple(community == 'beta' and point == 'selection' for point in SCENES))
    assert values(doc, model, DOMAIN, SCENES) == [False]


def test_later_withdrawal_of_selection_cannot_remove_a_selected_community():
    doc = setup(core(), 'source'); model = model_for(doc, protects=False)
    # The initial selection persists for this policy's target scope even though
    # the selecting condition is false in the evaluated actual situation.
    assert values(doc, model, DOMAIN, SCENES) == [False]
    model['jvanchor'] = lambda: 'actual'
    assert values(doc, model, DOMAIN, SCENES) == [True]


def test_factor_names_are_not_the_meanings_of_policy_and_threat():
    doc = setup(core(), 'link'); model = model_for(doc)
    model['jvfactor'] = lambda: 't'; model['jvthreatfactor'] = lambda: 'p'
    def renamed_index(state): return 4 * int(state('t')) + 2 * int(state('p')) + int(state('s'))
    model['jveq'] = lambda variable, state: PROTECT[renamed_index(state)] if variable == 's' else False
    model['jvworld'] = lambda state: SCENES[renamed_index(state) + 2]
    assert values(doc, model, DOMAIN, SCENES) == [True] * 4


def test_evidence_and_parent_remain_unchanged_and_completion_is_not_claimed():
    result = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-community-protection.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 8
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert result['effects']['equation_tables'] == 256
    assert result['proposals']['unknown_policy_contents_not_executed']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
