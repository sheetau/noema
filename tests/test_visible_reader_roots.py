"""Compare lookup behavior, mutations, custom accessors and scope restoration."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import pytest
from scripts.visible_lexical_script import _glyph,_shape_set
from scripts.visible_syntax import Reader
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_reader_roots import root_lookup_scope


def tables(reader):
    return {name:getattr(reader,name) for name in ('families','modifiers','keywords','names','roots')}


def test_same_tables_words_and_unknown_rejection():
    vocabulary=Vocabulary();expected=Reader([],vocabulary)
    with root_lookup_scope():
        actual=Reader([],vocabulary)
        assert actual.v is vocabulary and tables(actual)==tables(expected)
        for token,name in expected.roots.items():
            assert Reader([token],vocabulary).word()==Reader([token],expected.v).word()
            assert Reader([token],vocabulary).word().parts==(name,)
        with pytest.raises(ValueError,match='Unknown visible name'):
            Reader([('unknown-shape',)],vocabulary).word()
    assert vocabulary.document()==vocabulary._document


def test_changed_forms_are_observed_without_cached_passes():
    vocabulary=Vocabulary();name=next(iter(vocabulary._document['entries']))
    before=deepcopy(vocabulary._document)
    with root_lookup_scope():
        first=Reader([],vocabulary)
        form=vocabulary._document['entries'][name]['form']
        form['ray']=0 if form['ray'] is None else None
        actual=Reader([],vocabulary)
    expected=Reader([],vocabulary)
    assert tables(actual)==tables(expected) and actual.roots!=first.roots
    assert _shape_set(_glyph(form)['shapes']) in actual.roots
    vocabulary._document=before


def test_custom_document_accessor_keeps_original_path():
    class Custom(Vocabulary):
        def document(self):
            result=super().document()
            result['entries']={}
            return result
    vocabulary=Custom();expected=Reader([],vocabulary)
    with root_lookup_scope():
        actual=Reader([],vocabulary)
    assert actual.v is vocabulary and tables(actual)==tables(expected)
    assert actual.roots=={}


def test_scope_restores_on_failure_and_rejects_other_thread():
    original=Reader.__init__;vocabulary=Vocabulary()
    with pytest.raises(RuntimeError,match='scope probe'):
        with root_lookup_scope():
            with ThreadPoolExecutor(max_workers=1) as pool:
                with pytest.raises(ValueError,match='another thread'):
                    pool.submit(Reader,[],vocabulary).result()
            raise RuntimeError('scope probe')
    assert Reader.__init__ is original
