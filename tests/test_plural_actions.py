from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document, Content, SequenceValue
from scripts.check_plural_actions import setup, model_for, values, attribution_checks, full_domain_refusal, DOMAIN, SCENES
from scripts.compose_plural_actions import ROOT, PARENT, SOURCE, CORE, BASIS, INPUTS, FIELD_SYMBOLS, build_documents, basis
from scripts.compose_limits import call as k


@pytest.mark.parametrize('differences', list(product((False, True), repeat=2)))
def test_all_personal_presentations_but_only_some_divergence_is_required(differences):
    assert values(differences=differences) == [True] * 5 + list(differences) + [any(differences), True, False, False, True]


@pytest.mark.parametrize('missing', list(product(('presentation', 'intent', 'judgment'), (0, 1))))
def test_each_frame_must_have_its_own_judgment_presentation_and_intent(missing):
    assert values(missing=missing) == [True] * 3 + [missing[1] != i for i in (0, 1)] + [True, False, False, True, False, False, True]


@pytest.mark.parametrize('variant', ('empty', 'no_collection', 'foreign_member', 'role_mismatch'))
def test_source_eligibility_requires_nonempty_selected_owned_frames_and_same_role(variant):
    assert values(variant=variant) == [True] * 6 + [False, variant != 'empty', False, False, False, True]


@pytest.mark.parametrize('flags', list(product((False, True), repeat=3)))
def test_permissions_for_parts_and_compound_are_independent(flags):
    assert values(permissions=flags)[-3:] == list(flags)


@pytest.mark.parametrize('prohibited', (0, 1, 2))
def test_opposite_requirement_blocks_only_its_exact_target(prohibited):
    assert values(permissions=(True, True, True), prohibited=prohibited)[-3:] == [i != prohibited for i in range(3)]


def test_unknown_members_are_not_replaced_by_an_empty_collection():
    with pytest.raises(ValueError, match='Collection members are unknown'):
        values(variant='unknown_members')


@pytest.mark.parametrize('difference', (False, True))
def test_singleton_retains_truth_of_previous_divergent_action(difference):
    data = setup(); doc = deepcopy(data['document']); doc['statements'] = doc['statements'][:2]
    doc = parse(format_graph(doc, 'compact') + 'q[' + data['truth'](data['target']) + '].q[' + data['truth'](data['original'][0]) + '].')
    staged = {**data, 'document': doc}; model = model_for(staged, differences=(difference, False))
    model['hzlframes'] = lambda collection, anchor: SequenceValue(('entry',), '"individual"')
    result = evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model, max_steps=60_000_000)
    assert [x['value'] for x in result] == [True, True, difference, difference]


def test_individual_target_is_not_the_exact_combined_target():
    data = setup(); doc = deepcopy(data['document']); doc['statements'] = doc['statements'][:2]
    expression = k('hzleligible', k('jzperson'), k('jzactivity'), data['singles'][0], k('jzanchor'))
    doc = parse(format_graph(doc, 'compact') + 'q[' + expression + '].')
    staged = {**data, 'document': doc}
    result = evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model_for(staged), max_steps=60_000_000)
    assert [x['value'] for x in result] == [True, True, False]


def combination_fixture():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] in ('rqn', 'rqo', 'rqk', 'rql')]
    doc['statements'] = []
    head = format_graph(doc, 'compact') + 'r jpleft[a a] e.r jpright[a a] e.r jpperson[] a.r jpact[] a.r jppoint[] d.'
    seq = 'l[i[h[a a] e]][r[p jpleft] r[p jpright]]'
    truth = lambda desc: 't[c[s[' + desc + ']][k jpperson[] k jpact[]]][k jppoint[]]'
    queries = [truth(k('rqk', seq)), truth(k('rql', seq)), truth(k('rqk', 'l[i[h[a a] e]][]')), truth(k('rql', 'l[i[h[a a] e]][]'))]
    return parse(head + ''.join('q[' + x + '].' for x in queries))


@pytest.mark.parametrize('left,right', list(product((False, True), repeat=2)))
def test_conjunction_disjunction_and_empty_identities(left, right):
    doc = combination_fixture()
    model = dict(jpleft=lambda person, act: Content(('s',), (left,)), jpright=lambda person, act: Content(('s',), (right,)),
        jpperson=lambda: 'person', jpact=lambda: 'act', jppoint=lambda: 's')
    assert [r['value'] for r in evaluate_document(doc, individuals=('person', 'act'), situations=('s',), primitives=model)] == [left and right, left or right, True, False]


@pytest.mark.parametrize('axis', (0, 1, 2))
def test_cannot_combine_different_people_acts_or_contexts(axis):
    doc = combination_fixture(); fixed = ('person', 'act', 's'); altered = list(fixed); altered[axis] = ('other', 'otheract', 't')[axis]
    def content(target):
        return lambda person, act: Content(('s', 't'), tuple((person, act, point) == tuple(target) for point in ('s', 't')))
    model = dict(jpleft=content(fixed), jpright=content(altered), jpperson=lambda: 'person', jpact=lambda: 'act', jppoint=lambda: 's')
    assert [r['value'] for r in evaluate_document(doc, individuals=('person', 'other', 'act', 'otheract'), situations=('s', 't'), primitives=model)] == [False, True, True, False]


@pytest.mark.parametrize('path', (SOURCE, CORE))
def test_attribution_is_nonfactive_and_full_description_domain_is_not_sampled(path):
    doc = parse((ROOT / path).read_text(encoding='utf-8'))
    assert len(attribution_checks(doc)) == 2
    assert 'description domain' in full_domain_refusal(doc)


def test_reproduction_parent_preservation_and_actual_dependencies():
    texts, evidence = build_documents()
    assert all((ROOT / p).read_text(encoding='utf-8') == text for p, text in texts.items())
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis(evidence)
    parent, source, core = [parse((ROOT / p).read_text(encoding='utf-8')) for p in (PARENT, SOURCE, CORE)]
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    assert len(source['statements']) == len(parent['statements']) == 16
    names = {d['name'] for d in core['declarations']}
    assert {'rqh', 'rqi', 'rqj', 'rqk', 'rql', 'rqm', 'rqn', 'rqo', 'rqp', 'hzleligible', 'hzlclaim'} <= names
    assert not {'rqd', 'rqe', 'rqf', 'rqg', 'hzkeligible', 'hzkclaim', 'hzjc'} & names
