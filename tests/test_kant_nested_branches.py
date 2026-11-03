import pytest

from scripts.check_kant_nested_branches import cases,checked,fixture,measure
from scripts.kant_public_fragment import compile_statement,decode,events
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.visible_syntax_geometry import to_svg,from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_recursive_svg_branch_preserves_native_syntax(index):
    row=checked(index)
    assert row['nested_forks']>=1
    assert row['max_branch_depth']>=2
    assert row['unbranched_paths']==[]


def test_four_branch_levels_are_read_from_actual_ink():
    row=checked(len(cases())-1)
    assert row['nested_forks']==3 and row['max_branch_depth']==4
    with pytest.raises(ValueError,match='cannot fork'):
        decompose_flow(read_geometry(from_svg(row['svg'])),terminal_words=True,
            branch_seams=True,large_branches=True,local_continuation=True)


def test_nested_and_flattened_layouts_recover_the_same_expression():
    context,_,_=fixture();row=checked(len(cases())-1)
    flat=compile_statement(row['source'],lexicon=context,nested=False)
    svg=to_svg(flat['shapes'])
    assert svg!=row['svg'] and measure(svg)['nested_forks']==0
    assert decode(from_svg(svg),lexicon=LexicalContext.from_published(context.published()))==row['source']


def test_inner_argument_order_and_binding_position_are_distinct():
    for a,b in ((0,1),(2,3)):
        assert checked(a)['svg']!=checked(b)['svg']
        assert checked(a)['source']!=checked(b)['source']


def test_recursive_reader_does_not_call_the_writer(monkeypatch):
    row=checked(len(cases())-1);context,_,_=fixture()
    def forbidden(*args,**kwargs):raise AssertionError('Reading must not regenerate the source')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    assert decode(list(reversed(from_svg(row['svg']))),
        lexicon=LexicalContext.from_published(context.published()))==row['source']


def test_shared_argument_is_not_lost_when_nested_inside_another_branch():
    context,_,_=fixture();row=checked(5)
    with use_context(context):stream=events(row['source'])
    def tokens(chain):
        for e in chain:
            yield e['token']
            if isinstance(e['side'],list):yield from tokens(e['side'])
    assert 'and_shared' in list(tokens(stream))
    assert row['nested_forks']==1


@pytest.mark.parametrize('extra',[False,True])
def test_inner_branch_cannot_borrow_or_leave_an_expression(extra):
    from scripts.kant_interleaved_layout import compile_stream
    context,_,_=fixture()
    with use_context(context):
        stream=events(cases()[0][2])
        inner=next(e for e in stream[0]['side'] if isinstance(e['side'],str))
        token=inner['side']
        tail=dict(token='not',side=None,depth=3,path=[1,1])
        inner['side']=([dict(token=token,word=token,side=None,depth=3,path=[1,1])]
            if extra else [])+[tail]
        drawing=compile_stream(stream,contacts=False)
    with pytest.raises(ValueError,match='exactly one complete expression|Incomplete visible expression'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=LexicalContext.from_published(context.published()))
