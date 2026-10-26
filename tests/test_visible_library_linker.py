from copy import deepcopy
import pytest

from scripts.check_visible_specialist_library import (
    core, library, authored, source, restored, answers, aliases, specialist_names, authoring_vocabulary)
from scripts.visible_library_linker import link
from scripts.visible_word_forms import Word, symbol
from scripts.visible_collection import body_stream, CollectionReader
from scripts.shared_modality import call, op
from scripts.shared_reference import definition


def test_all_specialists_are_inline_and_only_core_is_needed_to_decode():
    result = restored()
    assert len(specialist_names()) == 49
    assert len(result['document']['declarations']) == 55
    assert sum(d['name'] not in core()._by_symbol for d in result['document']['declarations']) == 51
    assert answers(result['document'])


def test_link_only_needed_dependencies_and_keep_equal_quoted_names_separate():
    doc = link(authored(), [library()], vocabulary=core())
    assert len(doc['declarations']) == 4  # components, rational order and two local aliases
    assert set(aliases()) <= {d['name'] for d in doc['declarations']}
    assert doc['statements'] == source()['statements']
    assert answers(doc)  # evaluator requires exactly the declared primitives


def test_library_order_and_duplicate_identical_libraries_do_not_change_output():
    subset = deepcopy(library())
    subset['declarations'] = authoring_vocabulary().imports({'vectorcomponents'})
    expected = link(authored(), [library()], vocabulary=core())
    assert link(authored(), [library(), subset], vocabulary=core()) == expected
    assert link(authored(), [subset, library(), library()], vocabulary=core()) == expected


def test_conflicting_definition_and_primitive_rejected_even_when_unused():
    doc = deepcopy(authored()); name = aliases()[0]
    doc['declarations'].append(deepcopy(doc['declarations'][0]))
    with pytest.raises(ValueError, match='Repeated'):
        link(doc, [library()], vocabulary=core())
    doc = deepcopy(authored()); doc['declarations'][0] = dict(kind='primitive', name=name, parameters=[], result='truth')
    with pytest.raises(ValueError, match='Non-core primitive'):
        link(doc, [library()], vocabulary=core())
    doc = deepcopy(authored()); old = deepcopy(library()['declarations'][-1]); old['body'] = op('not', old['body'])
    doc['declarations'].append(old)
    with pytest.raises(ValueError, match='Conflicting'):
        link(doc, [library()], vocabulary=core())


def test_unknown_cyclic_and_changed_core_are_rejected():
    a, b = aliases(); doc = deepcopy(authored())
    doc['declarations'][0]['body'] = call(b); doc['declarations'][1]['body'] = call(a)
    with pytest.raises(ValueError, match='Cyclic'):
        link(doc, [library()], vocabulary=core())
    doc = deepcopy(authored()); doc['statements'].append(dict(kind='ask', body=call(symbol(Word('compound', ('rain', 'round', 'fly')), core()))))
    with pytest.raises(ValueError, match='Unknown dependency'):
        link(doc, [library()], vocabulary=core())
    doc = deepcopy(authored()); d = core().declaration('rationalbelow'); d['result'] = 'individual'; doc['declarations'].append(d)
    with pytest.raises(ValueError, match='Core meaning changed'):
        link(doc, [library()], vocabulary=core())


def test_library_assertions_cannot_be_silently_imported():
    bad = deepcopy(library()); bad['statements'] = source()['statements'][:4]
    with pytest.raises(ValueError, match='silently add assertions'):
        link(authored(), [bad], vocabulary=core())


def test_removing_a_definition_cannot_be_repaired_by_a_specialist_name_table():
    doc = deepcopy(source()); name = authoring_vocabulary()._symbols['vectorcomponents']
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] != name]
    with pytest.raises(ValueError):
        body_stream(doc, core())


def test_existing_collection_reader_can_read_without_linker_metadata():
    tokens, _, _, doc = body_stream(source(), core())
    assert CollectionReader(tokens, core()).document() == doc
