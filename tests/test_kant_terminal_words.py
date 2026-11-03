from copy import deepcopy

import pytest

from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.kant_public_fragment import compile_statement,decode,events,side_slot
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.visible_word_forms import Word,symbol
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,quote


def fixture_context():
    name=symbol(Word('compound',('red','book','treeone')),vocabulary())
    document=dict(schema_version='0.16',lexicon_version='0.16',statements=[],declarations=[
        dict(kind='definition',name=name,parameters=[],result='individual',body=call('book'))])
    spelling={name:dict(parts=['book','aki'],meaning_ja='この例の本を指す公開された別名。')}
    return name,LexicalContext(document,declared_spellings=spelling)


@pytest.mark.parametrize('quoted',[False,True])
def test_a_closed_compound_word_can_be_one_terminal_argument(quoted):
    name,ctx=fixture_context()
    body=call('give',call('aki'),dict(kind='call',symbol=name,arguments=[]),call('home'))
    if quoted:body=logic('equal',quote(body),quote(body))
    with use_context(ctx):source=canonical(body)
    attached=compile_statement(source,lexicon=ctx)
    linear=compile_statement(source,lexicon=ctx,branch=False)
    assert any(len(g['side_centers'])==2 for g in attached['groups'])
    reader=LexicalContext.from_published(ctx.published())
    for drawing in (attached,linear):
        assert decode(from_svg(to_svg(drawing['shapes'])),lexicon=reader)==source
    flow=decompose_flow(read_geometry(attached['shapes']),terminal_words=True,
        branch_seams=True,large_branches=True)
    assert any(len(chain)==2 for chain in flow['side'])
    assert to_svg(attached['shapes'])!=to_svg(linear['shapes'])


def test_multi_circle_branch_does_not_need_a_writer_or_element_order(monkeypatch):
    name,ctx=fixture_context()
    with use_context(ctx):source=canonical(logic('equal',call('book'),dict(kind='call',symbol=name,arguments=[])))
    g=compile_statement(source,lexicon=ctx)
    def forbidden(*args,**kwargs):raise AssertionError('Reader must not regenerate the source')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    assert decode(list(reversed(from_svg(to_svg(g['shapes'])))),lexicon=ctx)==source


def test_shared_compound_argument_expands_to_the_same_two_calls():
    name,ctx=fixture_context();subject=dict(kind='call',symbol=name,arguments=[])
    with use_context(ctx):source=canonical(logic('and',call('red',subject),call('round',subject)))
    g=compile_statement(source,lexicon=ctx)
    assert g['groups'][0]['token']=='and_shared'
    assert len(g['groups'][0]['side_centers'])==2
    assert decode(from_svg(to_svg(g['shapes'])),lexicon=ctx)==source


def test_explicit_spelling_cannot_shadow_a_published_compound():
    name,ctx=fixture_context();declarations=ctx.document
    with pytest.raises(ValueError,match='collides'):
        LexicalContext(declarations,declared_spellings={name:dict(parts=['book','home'],meaning_ja='衝突する名前')})


def test_context_parameter_position_comes_from_the_public_signature():
    name,ctx=fixture_context()
    signatures=[['individual','situation','individual','situation'],['situation','individual','individual']]
    with use_context(ctx):
        for signature in signatures:
            ctx.words[name][1]['parameters']=signature
            assert side_slot(name)==max(i for i,t in enumerate(signature) if t=='situation')
        ctx.words[name][1]['parameters']=['individual']*3
        assert side_slot(name)==1


def test_declared_spelling_preserves_original_name_and_definitions():
    name,ctx=fixture_context()
    plain=LexicalContext(ctx.document)
    assert ctx.declarations==plain.declarations
    assert ctx.spellings[ctx.parts[name]]==name
    assert ctx.spellings[plain.parts[name]]==name
    corrupt=deepcopy(ctx.published());corrupt['declared_spellings'][name]['parts']=['book','nao']
    with pytest.raises(ValueError,match='dictionary spelling'):
        LexicalContext.from_published(corrupt)
