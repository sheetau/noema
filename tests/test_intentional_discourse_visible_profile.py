"""Retain typed attitude/quotation boundaries in actual visible geometry."""
from copy import deepcopy
import pytest
from noema.constructed_discourse import normalize_document
from scripts import intentional_discourse_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_all_contracts_survive_actual_svg():
    vocabulary=profile.IntentionalDiscourseVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.ALL_CONTRACTS)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','nao')),vocabulary,payload=768)['pages']
    restored=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert restored==document and len(restored['declarations'])==12


def test_goal_content_and_goal_description_are_not_interchangeable():
    vocabulary=profile.IntentionalDiscourseVisibleVocabulary()
    actual=deepcopy(vocabulary.declaration('sufficientgoalcourage'))
    parameters=[dict(name=n,sort=deepcopy(s)) for n,s in zip(('va','vb','vc'),actual['parameters'],strict=True)]
    assert parameters[1]['sort']['kind']=='description'
    parameters[1]['sort']='content'
    invalid=dict(kind='definition',name='wronggoal',parameters=parameters,result='truth',
        body=dict(kind='call',symbol=actual['name'],arguments=[dict(kind='variable',name=p['name']) for p in parameters]))
    with pytest.raises(ValueError):
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[actual,invalid],statements=[]))


def test_quoted_addressee_depends_on_each_reference_slot():
    # Two distinct values for each slot; no recipient facts or truth defaults.
    ref=profile.QuotedAddresseeReferences({('document','quote','context'):'interpreted-reader'})
    assert ref.reference('document','quote','context')=='interpreted-reader'
    for slot in range(3):
        values=['document','quote','context'];values[slot]='other'
        with pytest.raises(ValueError,match='Unknown quoted addressee'):ref.reference(*values)
