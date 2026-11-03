from copy import deepcopy

import pytest

from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary
from scripts.kant_public_fragment import compile_statement,decode,events,shared_slot
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,quote,quant,variable
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import to_svg,from_svg


def fixture():
    names=[symbol(Word('compound',(root,'book','treeone')),vocabulary())
           for root in ('red','round','home','town')]
    signatures=[(['situation','individual','situation'],'truth'),
                (['situation','individual'],'truth'),([], 'situation'),([], 'situation')]
    declarations=[dict(kind='primitive',name=n,parameters=p,result=r)
                  for n,(p,r) in zip(names,signatures)]
    ctx=LexicalContext(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=declarations,statements=[]),declared_spellings={
            names[2]:dict(parts=['home','book'],meaning_ja='試験用の状況参照。')})
    def apply(i,*args):return dict(kind='call',symbol=names[i],arguments=list(args))
    return ctx,apply,names


@pytest.mark.parametrize('wrapper',['bare','quote','binder','nested'])
def test_shared_context_restores_each_public_slot_and_remaining_argument_order(wrapper):
    ctx,apply,names=fixture()
    individual=variable('x') if wrapper=='binder' else call('book')
    body=logic('and',apply(0,apply(3),individual,apply(2)),apply(1,apply(2),call('home')))
    if wrapper=='quote':body=logic('equal',quote(body),quote(body))
    if wrapper=='binder':body=quant('forall','x',body)
    if wrapper=='nested':body=logic('and',call('red',call('book')),body)
    with use_context(ctx):
        source=canonical(body)
        assert (shared_slot(names[0]),shared_slot(names[1]))==(2,0)
        assert any(e['token']=='and_shared' for e in events(source))
    reader=LexicalContext.from_published(ctx.published())
    for sharing in (True,False):
        drawing=compile_statement(source,lexicon=ctx,sharing=sharing)
        assert decode(list(reversed(from_svg(to_svg(drawing['shapes'])))),lexicon=reader)==source


def test_different_contexts_or_only_an_earlier_common_context_do_not_share():
    ctx,apply,_=fixture()
    pairs=[(apply(0,apply(2),call('book'),apply(3)),apply(1,apply(2),call('home'))),
           (apply(1,apply(2),call('book')),apply(1,apply(3),call('book')))]
    with use_context(ctx):
        for pair in pairs:
            assert not any(e['token']=='and_shared' for e in events(canonical(logic('and',*pair))))


def test_shared_head_rejects_a_predicate_without_a_shared_role():
    ctx,apply,names=fixture()
    with use_context(ctx):
        source=canonical(logic('and',apply(1,apply(2),call('book')),apply(1,apply(2),call('home'))))
    drawing=compile_statement(source,lexicon=ctx)
    reader=LexicalContext.from_published(ctx.published())
    reader.words[names[1]][1]['parameters']=['individual','individual']
    with pytest.raises(ValueError,match='public shared role'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=reader)


def test_shared_context_cannot_capture_an_ambient_binding_through_quote():
    ctx,apply,_=fixture()
    body=logic('and',apply(1,apply(2),variable('x')),apply(1,apply(2),call('book')))
    source=dict(kind='assert',body=quant('forall','x',logic('equal',quote(body),quote(body))))
    with pytest.raises(ValueError):
        compile_statement(source,lexicon=ctx)
