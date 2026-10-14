from copy import deepcopy
from itertools import product
import json

import pytest

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from noema.extraction import _references
from scripts.compose_constructed_actions import ROOT, PARENT, SOURCE, CORE, BASIS, INPUTS, build_documents, basis
from scripts.check_constructed_actions import setup, values, model_for, source_eligibility_case, full_domain_refusal, DOMAIN, SCENES
from scripts.compose_limits import call as k


@pytest.fixture(scope='module')
def data():
    return setup()


@pytest.mark.parametrize('performed,intended,permitted,reviewed', list(product((False, True), repeat=4)))
def test_existing_and_constructed_actions_agree_without_conflating_permission_or_purpose(data, performed, intended, permitted, reviewed):
    actual = performed and intended
    assert values(data, performed=performed, intended=intended, permitted=permitted, reviewed=reviewed) == [True, actual, actual, True, True, permitted, reviewed]


@pytest.mark.parametrize('variant', ('other_judge', 'other_issue', 'other_standard', 'empty_candidates',
    'other_message', 'other_goal', 'other_voice', 'outsider', 'not_scholar'))
def test_existing_semantic_conditions_survive_construction(data, variant):
    assert values(data, variant=variant) == [True, False, False, True, True, True, False]


@pytest.mark.parametrize('variant', ('other_permitted_target', 'public_prohibited'))
def test_permission_checks_the_exact_same_constructed_action(data, variant):
    assert values(data, variant=variant) == [True, True, True, True, True, False, False]


@pytest.mark.parametrize('variant', ('no_frame', 'role_mismatch'))
def test_frame_selection_and_permission_role_are_required_by_eligibility(data, variant):
    assert values(data, variant=variant) == [True, True, True, True, False, True, False]


def test_constructing_and_matching_does_not_execute_the_action(data):
    doc = deepcopy(data['document']); doc['statements'] = [doc['statements'][3]]
    def forbidden(*args):
        raise AssertionError('Action or criteria were executed during construction')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    assert evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model) == [{'kind': 'ask', 'value': True}]


@pytest.mark.parametrize('position', (0, 2))
def test_a_template_function_code_pair_cannot_be_mixed_in_an_accepted_target(data, position):
    # rqd is a low-level template. Only rqe binds each function to the very same
    # description. A manually constructed mismatched pair must fail rqf.
    doc = deepcopy(data['document']); doc['statements'] = []
    constructor = deepcopy(next(d for d in doc['declarations'] if d['name'] == 'rqe'))
    constructor['name'] = 'jabadconstructor'
    names = {name: param['name'] for (name, _), param in zip(INPUTS, constructor['parameters'])}
    constructor['body']['arguments'][position] = {'kind': 'variable', 'name': names['standardcriterion' if position == 0 else 'owncriterion']}
    doc['declarations'].append(constructor)
    arguments = [data['arguments'][name] for name, _ in INPUTS]
    doc = parse(format_graph(doc, 'compact') + 'q[' + k('rqf', k('jabadconstructor', *arguments), *arguments) + '].')
    def forbidden(*args):
        raise AssertionError('A semantic interpretation was used to accept a mismatch')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    assert evaluate_document(doc, individuals=DOMAIN, situations=SCENES, primitives=model) == [{'kind': 'ask', 'value': False}]


def test_unknown_frame_selection_is_not_filled_with_false(data):
    model = model_for(data)
    def unknown(*args):
        raise ValueError('Frame selection is unknown')
    model['jaframes'] = unknown
    with pytest.raises(ValueError, match='Frame selection is unknown'):
        evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES, primitives=model, max_steps=60_000_000)


@pytest.mark.parametrize('variant,expected', [('baseline', True), ('no_frame', False), ('role_mismatch', False)])
def test_actual_manuscript_eligibility_definition_uses_selected_frame_and_permission_role(data, variant, expected):
    assert source_eligibility_case(data, variant) == [True, expected]


@pytest.mark.parametrize('path', (SOURCE, CORE))
@pytest.mark.parametrize('grant', (False, True))
def test_revised_attribution_uses_same_author_and_scope_without_execution(path, grant):
    doc = parse((ROOT / path).read_text(encoding='utf-8')); doc['statements'] = doc['statements'][-1:]
    def forbidden(*args):
        raise AssertionError('Attribution ran a quoted condition')
    def attributed(node, author, content, scope, context):
        assert (node, author, scope, context) == ('node', 'author', 'scope', 'context')
        assert content.rank == 1 and json.loads(content.syntax) == {'kind': 'call', 'symbol': 'hzkclaim', 'arguments': []}
        return grant
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(hzjn=attributed, hzjo=lambda: 'node', wa=lambda: 'author', hzjp=lambda: 'scope', wh=lambda: 'context')
    assert evaluate_document(doc, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model) == [{'kind': 'assert', 'value': grant}]


def test_actual_source_claim_reaches_constructor_and_does_not_use_opaque_eligibility():
    documents, evidence = build_documents()
    for path, text in documents.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source = parse(documents[SOURCE])
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements'][:-1]
    assert len(source['statements']) == len(parent['statements']) == 16
    core = parse(documents[CORE]); names = {d['name'] for d in core['declarations']}
    assert {'rqg', 'rqf', 'rqe', 'rqd', 'rqa', 'rqb', 'rpu', 'rpt', 'rpq', 'hzb4', 'hzu', 'hzx'} <= names
    assert 'hzjc' not in names and 'hzjq' not in names and 'hzjr' not in names
    assert not any(name.startswith('jtemplate') for name in names)
    assert evidence['disquotations_removed'] == 3
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis(documents, evidence)


@pytest.mark.parametrize('path', (SOURCE, CORE))
def test_actual_revised_claim_does_not_replace_all_descriptions_with_selected_frames(path):
    assert 'description domain' in full_domain_refusal(parse((ROOT / path).read_text(encoding='utf-8')))
