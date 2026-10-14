from copy import deepcopy
from itertools import product
import json

import pytest

from noema.grammar import parse as old_parse
from noema.ranked import parse
from noema.ranked_discourse import normalize_document
from noema.guarded_ranked_semantics import evaluate_document
from noema.semantics import SemanticError
from scripts.compose_quantified_permissions import ROOT, CORE, SOURCE, PARENT, BASIS, build_documents, basis
from scripts.check_quantified_permissions import finite_instances, instance_values, model_for, PEOPLE, SCENES


@pytest.fixture(scope='module')
def finite():
    return finite_instances(parse((ROOT / CORE).read_text(encoding='utf-8')))


@pytest.mark.parametrize('permissions,fulfilled', list(product(product((False, True), repeat=2), repeat=2)))
def test_actual_composed_body_distinguishes_both_persons_duties_and_permissions(finite, permissions, fulfilled):
    assert instance_values(finite, permissions=permissions, fulfilled=fulfilled) == [True, *fulfilled,
        all(not duty or permission for duty, permission in zip(fulfilled, permissions))]


@pytest.mark.parametrize('variant,expected', [
    ('wrong_person', [True, True, True, False]),
    ('wrong_role', [True, True, True, False]),
    ('opposite_requirement', [True, True, True, False]),
    ('two_targets', [True, True, True, True]),
    ('wrong_alternative', [True, True, True, False]),
    ('empty_items', [True, False, False, True]),
    ('empty_cases', [True, False, False, True]),
    ('empty_population', [True, True, True, True]),
])
def test_content_alternatives_negative_requirements_and_vacuous_cases(finite, variant, expected):
    assert instance_values(finite, variant=variant) == expected


def test_exclusion_is_a_separate_group_not_the_speaker(finite):
    assert instance_values(finite, permissions=(True, False), variant='exclude_bob') == [True, True, True, True]
    assert instance_values(finite, permissions=(True, False)) == [True, True, True, False]


def test_full_description_domain_is_still_refused(finite):
    full = deepcopy(finite)
    original = parse((ROOT / CORE).read_text(encoding='utf-8'))
    originals = {d['name']: d for d in original['declarations']}
    full['declarations'] = [deepcopy(originals[d['name']]) if d['name'] in ('rpp', 'rpu') else d for d in full['declarations']]
    full = normalize_document(full)
    with pytest.raises(SemanticError, match='description domain'):
        evaluate_document(full, individuals=PEOPLE, situations=SCENES, primitives=model_for(full), max_steps=10_000_000)


def test_unknown_permission_is_not_false_or_an_omitted_case(finite):
    def unknown(*args):
        raise ValueError('Permission has no interpretation')
    model = model_for(finite); model['h7b'] = unknown
    with pytest.raises(ValueError, match='Permission has no interpretation'):
        evaluate_document(finite, individuals=PEOPLE, situations=SCENES, primitives=model, max_steps=10_000_000)


@pytest.mark.parametrize('path', (SOURCE, CORE))
@pytest.mark.parametrize('grant', (False, True))
def test_actual_author_attribution_is_scoped_and_does_not_execute_content(path, grant):
    doc = parse((ROOT / path).read_text(encoding='utf-8'))
    doc['statements'] = doc['statements'][-1:]
    calls = []
    def forbidden(*args):
        raise AssertionError('Quoted permission condition executed')
    def attributed(node, author, description, scope, context):
        assert (node, author, scope, context) == ('node', 'author', 'scope', 'context')
        assert description.rank == 1
        assert json.loads(description.syntax) == {'kind': 'call', 'symbol': 'hzjq', 'arguments': []}
        calls.append(True)
        return grant
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(hzjo=lambda: 'node', wa=lambda: 'author', hzjp=lambda: 'scope', wh=lambda: 'context', hzjn=attributed)
    assert evaluate_document(doc, individuals=('node', 'author', 'scope'), situations=('context',), primitives=model) == [{'kind': 'assert', 'value': grant}]
    assert calls == [True]


def test_parent_and_source_bindings_are_preserved_and_artifacts_reproduce():
    documents = build_documents()
    for path, text in documents.items():
        assert (ROOT / path).read_text(encoding='utf-8') == text
    parent = old_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    source = parse(documents[SOURCE])
    assert source['declarations'][:len(parent['declarations'])] == parent['declarations']
    assert source['statements'][:-1] == parent['statements']
    assert len(source['statements']) == 16
    assert json.loads((ROOT / BASIS).read_text(encoding='utf-8')) == basis(documents)
