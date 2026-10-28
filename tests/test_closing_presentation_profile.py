"""Visible closing references, field binding, and explicit unknown rejection."""
from fractions import Fraction
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import FunctionValue
from scripts import closing_presentation_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_closing_reference_types_survive_actual_svg():
    vocabulary=profile.ClosingPresentationVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports(set(profile.EXTRA)),statements=[]))
    pages=compile_collection(document,Word('proper',('book','home','nao')),vocabulary,payload=768)['pages']
    assert decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']==document
    assert vocabulary._symbols['presentationrecord']!=vocabulary._symbols['closingpresentationrecord']


def test_every_record_field_keeps_its_position():
    # Binding diagnostics: instantiate the other fields; vary one of four
    # fields over two values, and inspect all four selectors each time.
    for changed in range(4):
        values=['base']*4;values[changed]='changed'
        model=profile.ClosingPresentationReferences({('ctx',1):'signature'},{('ctx',1):values})
        assert model.reference('ctx',Fraction(1))=='signature'
        record=model.record('ctx',1)
        for selected in range(4):
            selector=FunctionValue(('individual',)*4,'individual',lambda *items,i=selected:items[i])
            assert record(selector)==values[selected]
        assert set(model.handlers())=={'closingreference','closingpresentationrecord'}


def test_unknown_location_and_unknown_record_remain_different():
    model=profile.ClosingPresentationReferences({('ctx',1):'signature',('ctx',2):'date'},
        {('ctx',1):('use','designation','author','document')})
    assert model.reference('ctx',2)=='date'
    for context,item in [('other',1),('ctx',3)]:
        with pytest.raises(ValueError):model.reference(context,item)
        with pytest.raises(ValueError):model.record(context,item)
    with pytest.raises(ValueError):model.record('ctx',2)
    with pytest.raises(ValueError):profile.ClosingPresentationReferences({}, {('ctx',1):('a','b','c','d')})
    with pytest.raises(ValueError):profile.ClosingPresentationReferences({('ctx',1):'x',('ctx',2):'x'}, {})
    with pytest.raises(ValueError):profile.ClosingPresentationReferences({('ctx',1):'x'}, {('ctx',1):('a','b','c')})


@pytest.mark.parametrize('item',[0,-1,Fraction(1,2),True,1.0,'1'])
def test_invalid_positions_are_not_coerced(item):
    model=profile.ClosingPresentationReferences({('ctx',1):'x'},{('ctx',1):('a','b','c','d')})
    with pytest.raises(ValueError):model.reference('ctx',item)
    with pytest.raises(ValueError):model.record('ctx',item)
    with pytest.raises(ValueError):profile.ClosingPresentationReferences({('ctx',item):'x'}, {})
