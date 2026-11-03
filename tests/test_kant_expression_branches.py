import pytest

from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_public_lexicon import vocabulary,mark_boundaries
from scripts.visible_word_forms import Word,symbol
from scripts.check_kant_public_fragment import canonical
from scripts.check_visible_syntax import call,logic,quant,variable,quote
from scripts.kant_public_fragment import compile_statement,decode,events
from scripts.kant_geometry_reader import read_geometry,recover_seams
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import to_svg,from_svg


from scripts.check_kant_expression_branches import fixture


@pytest.mark.parametrize('variant',['word-boundary','nested-logic','argument-order','quoted','bound'])
@pytest.mark.parametrize('contacts',[False,True])
def test_whole_expression_branch_recovers_exact_syntax(variant,contacts):
    ctx,f=fixture()
    rhs=f(0,call('book'))
    if variant=='nested-logic':rhs=logic('and',rhs,logic('not',f(2,call('aki'),call('nao'))))
    if variant=='argument-order':rhs=f(2,call('nao'),call('aki'))
    if variant=='bound':rhs=f(0,variable('x'))
    body=logic('or',call('rain',call('town')),rhs)
    if variant=='bound':body=quant('forall','x',body)
    if variant=='quoted':body=logic('equal',quote(body),quote(body))
    with use_context(ctx):source=canonical(body);stream=events(source)
    assert any(isinstance(e['side'],list) for e in stream)
    reader=LexicalContext.from_published(ctx.published())
    svgs=[]
    for enabled in (True,False):
        drawing=compile_statement(source,lexicon=ctx,contacts=contacts,subexpressions=enabled)
        svg=to_svg(drawing['shapes']);svgs.append(svg)
        assert decode(list(reversed(from_svg(svg))),lexicon=reader)==source
    assert svgs[0]!=svgs[1]
    if variant=='word-boundary':
        geo=read_geometry(from_svg(svgs[0]));flow=decompose_flow(geo,terminal_words=True,branch_seams=True)
        assert any(len(side)>=3 for side in flow['side']) and recover_seams(geo,branch_seams=True)


@pytest.mark.parametrize('extra',[False,True])
def test_a_branch_must_consume_exactly_one_complete_expression(monkeypatch,extra):
    ctx,f=fixture()
    with use_context(ctx):
        source=canonical(logic('or',call('rain',call('town')),f(0,call('book'))))
        stream=events(source)
        side=next(e['side'] for e in stream if isinstance(e['side'],list))
        if extra:
            token=call('book')['symbol']
            side.append(dict(token=token,word=token,side=None,depth=1,path=[1]))
            mark_boundaries(side)
        else:side.pop()
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args:stream)
    drawing=compile_statement(source,lexicon=ctx,contacts=False)
    with pytest.raises(ValueError,match='exactly one complete expression|Incomplete visible expression'):
        decode(drawing['shapes'],lexicon=LexicalContext.from_published(ctx.published()))


def test_interleaved_components_still_need_a_declared_compact_gap():
    from scripts import balanced_circle_script as b
    shapes=[b.circle(0,32,b.SMALL),b.circle(200,32,b.SMALL),b.circle(100,0,b.SMALL),
            b.line((b.SMALL,32),(200-b.SMALL,32))]
    with pytest.raises(ValueError,match='Interleaved'):
        recover_seams(read_geometry(shapes),branch_seams=True)


def test_two_alternative_compact_links_are_rejected():
    from scripts import balanced_circle_script as b
    span=2*b.MEDIUM+b.MIN_GAP
    shapes=[b.circle(x,y,b.MEDIUM) for x in (0,span) for y in (0,64)]
    shapes += [b.line((x,b.MEDIUM),(x,64-b.MEDIUM)) for x in (0,span)]
    with pytest.raises(ValueError,match='Ambiguous compact'):
        recover_seams(read_geometry(shapes),branch_seams=True)
