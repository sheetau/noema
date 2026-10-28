"""Distinguish frontmatter contexts, item positions, and target-free retrieval."""
from fractions import Fraction
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import frontmatter_reference_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_word_forms import Word
from scripts.visible_syntax_geometry import to_svg,from_svg


def test_every_lookup_slot_and_invalid_positions():
    reference=profile.FrontmatterReferences({('front',1):'title',('front',2):'author',('other',1):'other-title'})
    assert reference.reference('front',Fraction(1))=='title'
    assert reference.reference('front',2)=='author'
    assert reference.reference('other',1)=='other-title'
    for args in [('unknown',1),('front',3)]:
        with pytest.raises(ValueError,match='Unknown frontmatter'):reference.reference(*args)
    for bad in (0,-1,Fraction(1,2),True,1.0,'1'):
        with pytest.raises(ValueError,match='positive integer'):reference.reference('front',bad)
        with pytest.raises(ValueError,match='positive integer'):profile.FrontmatterReferences({('front',bad):'x'})
    with pytest.raises(ValueError,match='share a location'):
        profile.FrontmatterReferences({('front',1):'same',('front',2):'same'})


def test_native_reference_does_not_require_title_or_author_truth():
    def call(n,*args):return dict(kind='call',symbol=n,arguments=list(args))
    doc=profile.library()
    doc['declarations']+=[dict(kind='primitive',name='front',parameters=[],result='situation'),
                         dict(kind='primitive',name='expected',parameters=[],result='individual')]
    doc['statements']=[dict(kind='ask',body=dict(kind='equal',arguments=[
        call('frontmatterreference',call('front'),dict(kind='number',numerator=1,denominator=1)),call('expected')]))]
    reference=profile.FrontmatterReferences({('front',1):'location'})
    results=evaluate_document(normalize_document(doc),individuals=('location','other'),situations=('front','body'),
        primitives=reference.handlers()|{'front':lambda:'front','expected':lambda:'location'})
    assert results[0]['value'] is True


def test_frontmatter_reference_actual_svg_roundtrip():
    v=profile.FrontmatterReferenceVisibleVocabulary()
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports({'frontmatterreference'}),statements=[]))
    compiled=compile_collection(doc,Word('proper',('home','book')),v,payload=768)
    assert decode_collection([from_svg(to_svg(p['shapes'])) for p in compiled['pages']],v)['document']==doc
