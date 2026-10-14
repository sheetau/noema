import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from scripts.check_scoped_enablers import ROOT, REPORT, PARENT, PEOPLE, ACTORS, FIELDS, setup, generic_model, values
from scripts.compose_topical_enablement import POSSIBLE
from scripts.compose_limits import call as k, app, op, both, quant


def document():
    return setup((ROOT / 'examples/v014/scoped-enablers.noema').read_text(encoding='utf-8'))


def test_different_people_can_have_different_enablers_without_one_common_enabler():
    doc = document()
    refs = {**FIELDS, 'person': 'v person', 'enabler': 'v enabler'}
    per_person = op('y', app('p jkscope', 'v person'), both(
        app('p jleligible', 'v enabler', 'v person'), k('rlo', *(refs[n] for n, _ in POSSIBLE))))
    common = quant('g', 'enabler', 'a', quant('f', 'person', 'a', per_person))
    doc = parse(format_graph(doc, 'compact') + 'q[' + common + '].')
    assert values(doc, generic_model(doc)) == [True, False, True, True, False, False]


def test_unassessed_alternative_does_not_erase_a_known_success_but_blocks_a_shortfall_count():
    doc = document(); model = generic_model(doc, (False, False, True, True))
    available = model['jkavailable']
    def expanded(person, matter, plan, point):
        return available(person, matter, plan, point) or (
            person in PEOPLE and matter == 'matter' and plan == 'plan' and point == 'bad')
    model['jkavailable'] = expanded
    model['jkoutcomes'] = lambda person, matter, plan, start, end: expanded(person, matter, plan, start) and end == 'done'
    # Selection remains empty at bad: the resulting ability is unassessed.
    assert values(doc, model) == [True, False, False, True, False]
    # Excluding the unassessed actor is an explicit change of the question.
    model['jleligible'] = lambda actor, person: actor == 'mentor' and person in PEOPLE
    assert values(doc, model) == [True, False, True, True, False]


def test_one_method_with_a_known_success_and_an_unassessed_alternative():
    doc = document(); model = generic_model(doc)
    available = model['jkavailable']
    model['jkavailable'] = lambda person, matter, plan, point: available(person, matter, plan, point) or (
        person in PEOPLE and matter == 'matter' and plan == 'plan' and point == 'bad')
    model['jkoutcomes'] = lambda person, matter, plan, start, end: model['jkavailable'](person, matter, plan, start) and end == 'done'
    model['jleligible'] = lambda actor, person: actor == 'teacher' and person in PEOPLE
    model['jkeffects'] = lambda actor, person, plan, start, end: model['jkenabling'](actor, person, plan, start) and end in ('ready', 'bad')
    assert values(doc, model) == [True, False, False, True, False]


def test_target_person_can_be_the_enabler_when_the_scope_and_methods_say_so():
    doc = document(); model = generic_model(doc)
    model['jleligible'] = lambda actor, person: actor == person and person in PEOPLE
    model['jkenabling'] = lambda actor, person, plan, point: actor == person and person in PEOPLE and plan == 'plan' and point == 'now'
    model['jkeffects'] = lambda actor, person, plan, start, end: model['jkenabling'](actor, person, plan, start) and end == 'ready'
    assert values(doc, model) == [True, False, True, True, False]


def test_unknown_scope_is_not_an_empty_scope():
    doc = document(); model = generic_model(doc, eligible=())
    assert values(doc, model) == [True, False, True, False, True]
    def unknown(*args): raise ValueError('Eligible enablers unknown')
    model['jleligible'] = unknown
    with pytest.raises(ValueError, match='Eligible enablers unknown'):
        values(doc, model)


def test_current_capability_does_not_supply_a_missing_enabling_method():
    doc = document(); model = generic_model(doc, variant='no_methods', current=(True, True))
    assert values(doc, model) == [True, True, True, False, False]


def test_saved_evidence_keeps_the_parent_and_does_not_claim_new_source_coverage():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    for name, digest in report['source_sha256'].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    child = parse((ROOT / 'examples/v014/kant-scoped-enablers.noema').read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert len(child['declarations']) == len(parent['declarations']) + 6
    assert child['statements'] == parent['statements']
    previous = json.loads((ROOT / 'reports/topical-enablement-v1.json').read_text(encoding='utf-8'))
    old, new = previous['alignment']['segments'][0], report['alignment']['segments'][0]
    assert (new['unit'], new['range'], new['text']) == (old['unit'], old['range'], old['text'])
    assert report['new_primitives'] == report['new_author_statements'] == 0
    assert not report['alignment']['semantic_completion']
    assert report['verified_full_units'] == {'kant-1784': 0, 'einstein-1905': 0}
