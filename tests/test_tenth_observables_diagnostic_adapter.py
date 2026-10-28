"""Reject unreviewed fixture changes while preserving Native value identity."""
from copy import deepcopy
import pytest
import test_tenth_observables_physics_visible as adapter
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue


@pytest.fixture
def body(monkeypatch):
    cut = dict(kind='function', parameters=['number'], result='truth')
    document = normalize_document(dict(schema_version='0.14', lexicon_version='0.14', declarations=[
        dict(kind='primitive', name='bb', parameters=['number'], result=cut),
        dict(kind='primitive', name='p', parameters=['number', cut], result='truth'),
        dict(kind='definition', name='ek35', parameters=[], result='truth',
             body=dict(kind='exists', variable='vn', sort='number',
                       body=dict(kind='call', symbol='p', arguments=[
                           dict(kind='variable', name='vn'),
                           dict(kind='call', symbol='bb', arguments=[dict(kind='number', numerator=1, denominator=1)])])))
    ], statements=[]))
    monkeypatch.setattr(adapter, 'mapping', lambda: {})
    monkeypatch.setattr(adapter.check, 'restored', lambda: dict(document=deepcopy(document)))
    monkeypatch.setattr(adapter, 'RECOVERED_DEFINITIONS_SEEN', set())
    monkeypatch.setattr(adapter, 'DIAGNOSTIC_ONLY_SEEN', set())
    monkeypatch.setattr(adapter, 'TRANSFORMED_DEFINITIONS_SEEN', set())
    adapter.checked_extract_json.cache_clear()
    yield document
    adapter.checked_extract_json.cache_clear()


def abstract(document):
    result = adapter.binding_transform(document, 'jerunit', True)
    result['declarations'].insert(0, dict(kind='primitive', name='jerunit', parameters=[], result='individual'))
    return result


def test_binding_abstraction_requires_original_typed_body_first(body):
    with pytest.raises(AssertionError, match='Typed body was not checked first'):
        adapter.checked_extract(abstract(body), roots=['ek35'])
    adapter.checked_extract(body, roots=['ek35'])
    result = adapter.checked_extract(abstract(body), roots=['ek35']).document
    assert result['declarations'][-1]['body']['sort'] == 'individual'
    assert adapter.TRANSFORMED_DEFINITIONS_SEEN == {('ek35', 'ek35')}


def test_binding_abstraction_rejects_changed_argument_positions(body):
    adapter.checked_extract(body, roots=['ek35'])
    wrong = abstract(body)
    wrong['declarations'][-1]['body']['body']['arguments'].reverse()
    with pytest.raises(AssertionError, match='changed more than the declared abstraction'):
        adapter.checked_extract(wrong, roots=['ek35'])


def test_unlisted_transformation_rejects_changed_typed_body(body):
    wrong = deepcopy(body)
    wrong['declarations'][-1]['body']['kind'] = 'forall'
    with pytest.raises(AssertionError):
        adapter.checked_extract(wrong, roots=['ek35'])


def test_unknown_definition_is_not_treated_as_a_control(body):
    wrong = deepcopy(body)
    wrong['declarations'][-1]['name'] = 'unknown'
    with pytest.raises(KeyError):
        adapter.checked_extract(wrong, roots=['unknown'])


def test_native_unwrap_preserves_registered_callable_without_running_it(monkeypatch):
    calls = []
    def forbidden(*args):
        calls.append(args)
        raise AssertionError('Inspection executed a function')
    original = FunctionValue(('number',), 'truth', forbidden)
    nested = FunctionValue(original.parameters, original.result, original)
    def guard(raw):
        return FunctionValue(raw.parameters, raw.result, lambda *args: raw(*args))
    assert adapter.native_unwrap(guard(nested)) is original
    assert calls == []


def test_cloned_class_inherits_from_cloned_parent():
    derived = adapter.adapted_module('scripts.check_electron_transformed_dynamics')
    parent = adapter.adapted_module('scripts.check_electron_comoving_equations_v2')
    assert derived.Model.__bases__ == (parent.Model,)
    assert derived.Model.__init__.__globals__ is vars(derived)
    assert parent.Model.__init__.__globals__ is vars(parent)


def test_boundary_specialization_requires_original_body_and_exact_speed(body, monkeypatch):
    cut = dict(kind='function', parameters=['number'], result='truth')
    original = deepcopy(body)
    original['declarations'][-1].update(name='setb', body=dict(
        kind='forall', variable='speed', sort=cut,
        body=dict(kind='call', symbol='p', arguments=[
            dict(kind='number', numerator=1, denominator=1),
            dict(kind='variable', name='speed')])))
    original = normalize_document(original)
    monkeypatch.setattr(adapter.check, 'restored', lambda: dict(document=deepcopy(original)))
    specialized = deepcopy(original)
    specialized['declarations'][-1] = adapter.boundary_single_speed_transform(original['declarations'][-1])
    with pytest.raises(AssertionError, match='Typed body was not checked first'):
        adapter.checked_extract(specialized, roots=['setb'])
    adapter.checked_extract(original, roots=['setb'])
    adapter.checked_extract(specialized, roots=['setb'])
    assert ('single_speed_6','setb') in adapter.TRANSFORMED_DEFINITIONS_SEEN
    for wrong_speed in (5,7):
        wrong = deepcopy(specialized)
        wrong['declarations'][-1]['body']['arguments'][1]['arguments'][0]['numerator'] = wrong_speed
        with pytest.raises(AssertionError, match='changed more than the declared abstraction'):
            adapter.checked_extract(wrong, roots=['setb'])
    wrong = deepcopy(specialized)
    # Keep types valid so this probes the exact-transform guard, rather than
    # failing earlier at the grammar's argument-sort check.
    wrong['declarations'][-1]['body']['arguments'][0]['numerator'] = 2
    with pytest.raises(AssertionError, match='changed more than the declared abstraction'):
        adapter.checked_extract(wrong, roots=['setb'])


def test_candidate_checks_original_dependencies_before_abstraction(body, monkeypatch):
    from noema.grammar import format_graph
    text = format_graph(body, 'compact')
    adapter.native_candidate(text, 'q[k ek35[]].')
    assert 'ek35' in adapter.RECOVERED_DEFINITIONS_SEEN
    changed = deepcopy(body)
    changed['declarations'][-1]['body']['kind'] = 'forall'
    with pytest.raises(AssertionError):
        adapter.native_candidate(format_graph(changed, 'compact'), 'q[k ek35[]].')
