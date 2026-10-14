import hashlib
import json

import pytest

from noema.finite_semantics import Content, FunctionValue
from noema.grammar import parse
from scripts.check_observed_protection import REPORT, setup, model_for, values, DOMAIN, SCENES, prior
from scripts.compose_observed_protection import ROOT, PARENT


def core(): return (ROOT / 'examples/v014/observed-protection-core.noema').read_text(encoding='utf-8')


def test_matching_observations_do_not_identify_actual_and_hypothetical_situations():
    doc = setup(core(), 'individual'); model = model_for(doc)
    assert model['jvworld'](model['jorecords']('actual')) != 'actual'
    assert values(doc, model, DOMAIN, SCENES)[:5] == [True, True, True, True, False]


def test_each_community_keeps_its_own_observed_activity():
    doc = setup(core(), 'source'); model = model_for(doc)
    laws, activities, records = (model[n] for n in ('jvlaws', 'jvactivities', 'joobservations'))
    model['jvlaws'] = lambda community: FunctionValue(('individual', prior.STATE_SORT), 'truth',
        lambda variable, state: variable == 'p') if community == 'beta' else laws(community)
    model['jvactivities'] = lambda community: Content(SCENES, tuple(
        False if point == 'actual' else point.startswith('w') and point[3] == '1' for point in SCENES)) if community == 'beta' else activities(community)
    model['joobservations'] = lambda community, point: FunctionValue(('individual',), 'truth',
        lambda variable: variable == 'p') if community == 'beta' and point == 'actual' else records(community, point)
    assert values(doc, model, DOMAIN, SCENES) == [True, True]
    model['joobservations'] = lambda community, point: records('alpha', point)
    assert values(doc, model, DOMAIN, SCENES) == [True, False]


def test_old_observations_cannot_substitute_for_current_observations():
    doc = setup(core(), 'source'); model = model_for(doc)
    def records(community, point):
        return FunctionValue(('individual',), 'truth', lambda variable:
            variable == 's' or variable == 'p' and point == 'actual')
    model['joobservations'] = records
    assert values(doc, model, DOMAIN, SCENES) == [True, True]
    model['joobservations'] = lambda community, point: records(community, 'selection')
    assert values(doc, model, DOMAIN, SCENES) == [True, False]


def test_a_record_valid_only_under_an_intervention_is_not_an_actual_solution():
    doc = setup(core(), 'individual'); model = model_for(doc, variant='only_intervened_solution')
    assert values(doc, model, DOMAIN, SCENES) == [False] * 5 + [True, True]


def test_fitting_observations_do_not_supply_a_missing_protective_effect():
    doc = setup(core(), 'individual'); model = model_for(doc)
    model['jveq'] = lambda variable, state: variable in ('p', 's')
    assert values(doc, model, DOMAIN, SCENES) == [True, True, False, True, False, False, True]


def test_an_unmeasured_variable_is_not_filled_from_the_claimed_activity():
    doc = setup(core(), 'individual'); model = model_for(doc); records = model['jorecords']
    def unknown_record(point):
        known = records(point)
        def get(variable):
            if point == 'actual' and variable == 's': raise ValueError('Unmeasured activity variable')
            return known(variable)
        return FunctionValue(('individual',), 'truth', get)
    model['jorecords'] = unknown_record
    with pytest.raises(ValueError, match='Unmeasured activity variable'):
        values(doc, model, DOMAIN, SCENES)


def test_parent_and_saved_evidence_are_preserved_without_completion_claims():
    result = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in result['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-observed-protection.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 7
    assert child['statements'] == parent['statements'] and len(child['statements']) == 15
    assert result['new_primitives'] == result['new_author_statements'] == 0
    assert len(result['individual']['cases']) == 64
    assert result['proposals']['unknown_policy_and_observations_not_executed']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
