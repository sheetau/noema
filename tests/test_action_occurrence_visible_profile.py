"""Actual occurrence and author attribution remain independent after decoding."""
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import action_occurrence_visible_profile as profile
from scripts.visible_collection import compile_collection,decode_collection
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word


def test_occurrence_and_author_role_are_independent_in_actual_svg():
    vocabulary=profile.ActionOccurrenceVisibleVocabulary()
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=vocabulary.imports({'actionoccurrence','authordisplay'}),statements=[]))
    calls=[dict(kind='call',symbol=vocabulary._symbols['actionoccurrence'],arguments=[dict(kind='variable',name=n) for n in ('va','vd')]),
        dict(kind='call',symbol=vocabulary._symbols['authordisplay'],arguments=[dict(kind='variable',name=n) for n in ('va','vb','vc','vd')])]
    for body in calls:
        for name,sort in reversed([('va','individual'),('vb','individual'),('vc','individual'),('vd','situation')]):
            body=dict(kind='forall',variable=name,sort=sort,body=body)
        document['statements'].append(dict(kind='ask',body=body))
    document=normalize_document(document)
    pages=compile_collection(document,Word('proper',('book','home','round')),vocabulary,payload=768)['pages']
    restored=decode_collection([from_svg(to_svg(p['shapes'])) for p in pages],vocabulary)['document']
    assert restored==document
    for occurred in (False,True):
        for credited in (False,True):
            values={vocabulary._symbols['actionoccurrence']:lambda a,s:occurred,
                vocabulary._symbols['authordisplay']:lambda a,d,p,s:credited}
            result=evaluate_document(restored,individuals=('x','y'),situations=('now','other'),primitives=values)
            assert [r['value'] for r in result]==[occurred,credited]
