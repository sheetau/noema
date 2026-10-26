from copy import deepcopy
import pytest

from scripts.manuscript_transfer import (references, dependency_graph, closure, inventory,
                                        edition_candidate, mapping_specs, complete_mapping, build)


def call(name):
    return dict(kind='call', symbol=name, arguments=[])


def primitive(name):
    return dict(kind='primitive', name=name, parameters=[], result='truth')


def definition(name, body):
    return dict(kind='definition', name=name, parameters=[], result='truth', body=body)


def document():
    # identical bodies retain distinct names; a quotation still needs its source.
    return dict(schema_version='0.16', lexicon_version='0.16',
                declarations=[primitive('a'), primitive('unused'), definition('b', call('a')),
                              definition('c', call('a'))],
                statements=[dict(kind='ask', body=dict(kind='equal', arguments=[
                    dict(kind='quote', body=call('b')), dict(kind='quote', body=call('c'))]))])


def entries(doc):
    return {d['name']: dict(kind=d['kind'], declaration=d, meaning_basis='test', meaning_ja=d['name'])
            for d in doc['declarations']}


def test_quoted_only_references_are_retained_and_not_evaluated():
    doc = document(); graph = dependency_graph(doc)
    assert references(doc['statements']) == ({'b', 'c'}, {'b', 'c'})
    assert closure(references(doc['statements'])[0], graph) == {'a', 'b', 'c'}
    result = inventory(doc, entries(doc), {}, {})
    assert [r['symbol'] for r in result['declarations']] == ['a', 'unused', 'b', 'c']
    assert result['summary']['retained_unreferenced_primitives'] == 1
    assert result['declarations'][0]['statement_indices'] == [0]
    assert result['declarations'][1]['statement_indices'] == []


def test_quote_context_does_not_leak_to_sibling():
    value = [dict(kind='quote', body=call('a')), call('b'), dict(kind='function_ref', symbol='c')]
    assert references(value) == ({'a', 'b', 'c'}, {'a'})


@pytest.mark.parametrize('change', ['duplicate', 'forward', 'recursive', 'unknown_statement'])
def test_invalid_dependencies_rejected(change):
    doc = document()
    if change == 'duplicate':
        doc['declarations'].append(primitive('a'))
    elif change == 'forward':
        doc['declarations'][2]['body'] = call('c')
    elif change == 'recursive':
        doc['declarations'][2]['body'] = call('b')
    else:
        doc['statements'].append(dict(kind='ask', body=call('missing')))
    with pytest.raises(ValueError):
        dependency_graph(doc)


def test_unknown_closure_rejected():
    with pytest.raises(ValueError, match='Unknown dependency'):
        closure(['unknown'], dependency_graph(document()))


def test_matching_name_with_different_body_is_not_a_candidate():
    doc = document(); wrong = deepcopy(doc['declarations'][2]); wrong['body'] = call('unused')
    candidate = dict(declaration=wrong, shared_word='shared', semantic_replacement_authorized=False)
    result = inventory(doc, entries(doc), {}, {'b': [candidate]})
    assert result['declarations'][2]['structural_shared_candidates'] == []
    candidate['declaration'] = doc['declarations'][2]
    result = inventory(doc, entries(doc), {}, {'b': [candidate]})
    assert result['declarations'][2]['structural_shared_candidates'] == [
        dict(shared_word='shared', semantic_replacement_authorized=False)]
    assert len(result['declarations']) == 4
    assert not result['declarations'][2]['visible_spelling_assigned']


@pytest.mark.parametrize('change', ['missing', 'changed', 'unknown_designation'])
def test_inconsistent_documentation_rejected(change):
    doc = document(); es = deepcopy(entries(doc)); ids = {}
    if change == 'missing':
        del es['a']
    elif change == 'changed':
        es['b']['declaration']['body'] = call('unused')
    else:
        ids['missing'] = []
    with pytest.raises(ValueError):
        inventory(doc, es, ids, {})


def test_explicit_edition_candidate_preserves_quotation_and_source():
    doc = document(); doc['schema_version'] = doc['lexicon_version'] = '0.14'; saved = deepcopy(doc)
    result = edition_candidate(doc)
    assert doc == saved
    assert result['source_edition'] == '0.14' and result['target_edition'] == '0.16'
    assert result['declarations_and_statements_unchanged']
    assert not result['applied'] and not result['semantic_review_transferred']


def test_all_explicit_mapping_forms():
    basis = dict(source_renamings={'a': {'old': 'new'}},
                 preserved_definitions=[dict(document='b', names={'x': 'y'})],
                 preserved_sources=[dict(document='c', names=['z']),
                                    dict(document='d', renaming={'r': 's'})])
    assert mapping_specs(basis) == [('a', {'old': 'new'}), ('b', {'x': 'y'}),
                                   ('c', {'z': 'z'}), ('d', {'r': 's'})]


def test_inherited_rename_requires_matching_declaration_and_unique_target():
    a = primitive('a'); b = definition('b', call('a'))
    originals = dict(a=a, b=b)
    assert complete_mapping(originals, {'b': 'beta'}, [({'a': a}, {'a': 'alpha'})]) == dict(a='alpha', b='beta')
    different = dict(a, result='individual')
    assert complete_mapping(originals, {'b': 'beta'}, [({'a': different}, {'a': 'alpha'})]) == dict(b='beta')
    with pytest.raises(ValueError, match='Conflicting'):
        complete_mapping(originals, {'a': 'alpha'}, [({'a': a}, {'a': 'other'})])


def test_full_selected_inventory_and_baseline_preservation():
    result = build()
    for work, expected in [('kant-1784', (6061, 2120, 3941, 119, 4870)),
                           ('einstein-1905', (6255, 1857, 4398, 283, 5018))]:
        row = result['works'][work]; summary = row['summary']
        assert tuple(summary[k] for k in ('declarations', 'primitives', 'definitions', 'statements',
                                         'reachable_declarations')) == expected
        assert len(row['declarations']) == expected[0]
        assert all(not d['visible_spelling_assigned'] for d in row['declarations'])
        assert row['edition_candidate']['declarations_and_statements_unchanged']
    assert result['public_vocabulary'] == dict(edition=12, words=375, definitions=352, primitives=23)

