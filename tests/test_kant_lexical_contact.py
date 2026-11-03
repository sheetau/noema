import pytest

from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.kant_public_fragment import compile_statement,decode,forms
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_readable_flow import route
from scripts.balanced_circle_script import PITCH
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,quote
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import to_svg,from_svg


def fixture(parts=('book','aki')):
    name=symbol(Word('compound',('red','book','treeone')),vocabulary())
    ctx=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',statements=[],
        declarations=[dict(kind='definition',name=name,parameters=[],result='individual',body=call('book'))]),
        declared_spellings={name:dict(parts=list(parts),meaning_ja='既存の本を指す公開名。')})
    return ctx,dict(kind='call',symbol=name,arguments=[])


@pytest.mark.parametrize('placement',['main','side','shared','quoted'])
def test_contact_composition_restores_the_same_word_and_native_syntax(placement):
    ctx,word=fixture()
    if placement=='shared':body=logic('and',call('red',word),call('round',word))
    else:body=logic('equal',call('book'),word)
    if placement=='quoted':body=logic('equal',quote(body),quote(body))
    with use_context(ctx):source=canonical(body)
    reader=LexicalContext.from_published(ctx.published())
    counts=[]
    for contacts in (True,False):
        g=compile_statement(source,lexicon=ctx,contacts=contacts,branch=placement!='main')
        shapes=from_svg(to_svg(g['shapes']))
        counts.append(sum(r['kind']=='tangent' for r in read_geometry(shapes)['relations']))
        assert decode(list(reversed(shapes)),lexicon=reader)==source
    assert counts[0]>0 and counts[1]==0


def test_contact_does_not_chain_three_circles_or_repeat_per_word():
    ctx,word=fixture(('book','aki','book','nao'))
    with use_context(ctx):source=canonical(logic('equal',word,call('book')))
    drawing=compile_statement(source,lexicon=ctx,branch=False)
    geometry=read_geometry(drawing['shapes'])
    assert sum(r['kind']=='tangent' for r in geometry['relations'])==1
    assert decode(drawing['shapes'],lexicon=ctx)==source


def test_contact_cannot_replace_a_boundary_between_two_arguments():
    # Manually drawn equal(book, aki), with a contact across the argument boundary.
    equal=forms('equal',50,PITCH)[0]
    book=forms(call('book')['symbol'],170,0)[0]
    aki=forms(call('aki')['symbol'],202,PITCH)[0]
    shapes=equal['shapes']+book['shapes']+aki['shapes']
    link=route(equal['exit'],book['entry'],[s for s in shapes if s['kind']=='circle'],obstacles=shapes)
    assert link is not None
    shapes+=link[1]
    read_geometry(shapes)
    with pytest.raises(ValueError,match='one word'):
        decode(shapes)
