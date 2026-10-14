import hashlib
import json

import pytest

from noema.finite_semantics import Content
from noema.grammar import parse
from scripts import check_enlightening_epoch as epoch
from scripts.check_opening_opportunities import (
    ROOT, REPORT, PARENT, PEOPLE, SCENES, setup, source_setup,
    generic_model, source_model, values,
)


def data(source=False):
    stem = 'opening-opportunities-core' if source else 'opening-opportunities'
    text = (ROOT / ('examples/v014/' + stem + '.noema')).read_text(encoding='utf-8')
    return source_setup(text) if source else setup(text)


def test_already_having_an_opportunity_does_not_mean_it_is_opening_now():
    item = data()
    assert values(item, generic_model(item, (True, True, True, True))) == [True, False, False, False, False]


def test_a_new_option_can_replace_an_old_one_without_expanding_the_set():
    item = data(); model = generic_model(item)
    old = model['jropportunities']
    model['jractivities'] = lambda person, activity: person in PEOPLE and activity in ('plan', 'other')
    model['jropportunities'] = lambda person, activity: Content(SCENES, (True, True, False)) if activity == 'other' else old(person, activity)
    assert values(item, model) == [True, True, False, False, True]


def test_set_expansion_for_one_person_is_not_a_gain_for_everyone():
    item = data()
    assert values(item, generic_model(item, (False, True, True, True))) == [True, False, True, False, False]


def test_one_persons_gain_does_not_hide_another_persons_loss():
    item = data()
    assert values(item, generic_model(item, (False, True, True, False))) == [True, False, False, False, False]


def test_an_unassessed_old_option_blocks_a_claim_about_the_whole_scope():
    item = data(); model = generic_model(item)
    model['jractivities'] = lambda person, activity: person in PEOPLE and activity in ('plan', 'other')
    model['jrassessed'] = lambda person, activity, point: activity != 'other' or point != 'before'
    assert values(item, model) == [False] * 5


def test_endpoint_retention_does_not_assert_continuous_availability():
    item = data(); model = generic_model(item)
    old = model['jropportunities']
    model['jractivities'] = lambda person, activity: person in PEOPLE and activity in ('plan', 'other')
    model['jropportunities'] = lambda person, activity: Content(SCENES, (True, False, True)) if activity == 'other' else old(person, activity)
    assert values(item, model) == [True] * 5


@pytest.mark.parametrize('variant', ['no_process', 'wrong_person', 'ended'])
def test_endpoint_gain_does_not_supply_a_current_change_witness(variant):
    item = data()
    assert values(item, generic_model(item, variant=variant)) == [True, True, True, True, False]


def test_a_witness_for_another_activity_does_not_license_this_opportunity():
    item = data(); model = generic_model(item)
    model['jrprocesses'] = lambda person, activity: 'opening' if activity == 'other' else 'unrelated'
    assert values(item, model) == [True, True, True, True, False]


@pytest.mark.parametrize('start,end', [('now', 'before'), ('now', 'now')])
def test_reversed_or_identical_endpoints_do_not_describe_an_opening(start, end):
    item = data(); model = generic_model(item)
    model['jrstart'] = lambda: start; model['jrend'] = lambda: end
    assert values(item, model) == [False] * 5


def test_unknown_opportunity_assessment_is_not_completed_as_false():
    item = data(); model = generic_model(item)
    def unknown(*args): raise ValueError('Opportunity assessment unknown')
    model['jrassessed'] = unknown
    with pytest.raises(ValueError, match='Opportunity assessment unknown'):
        values(item, model)


def test_somebody_elses_goal_does_not_supply_this_persons_pursuit_opportunity():
    item = data(True); model = source_model(item)
    old = model['jmaims']
    model['jmaims'] = lambda person, act, goal, bindings, point: old(person, act, goal, bindings, point) and bindings.items == ('guide',)
    assert values(item, model) == [True, False, False, False, False, False, False, False]


def test_the_opening_can_be_quoted_without_evaluating_its_unknown_conditions():
    item, question, answer = epoch.discourse_setup(data(True))
    assert values(item, epoch.discourse_model(item, question, answer)) == [True]


def test_saved_evidence_preserves_history_and_leaves_semantic_completion_open():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-opening-opportunities.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 10
    assert child['statements'] == parent['statements']
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
