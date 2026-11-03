import pytest

from scripts.check_kant_multiple_arguments import cases,checked,fixture
from scripts.kant_public_fragment import compile_statement,decode,events,side_order
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import to_svg,from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_multiple_branches_preserve_order_types_and_scope(index):
    row=checked(index)
    assert row['multiple_owners']>=1 and row['maximum_sides']>=2
    assert row['branch_limits']==[] and row['unbranched_paths']==[]


def test_public_signature_fixes_each_branch_position():
    context,names=fixture()
    with use_context(context):
        assert side_order(names[0])==[0,2]
        assert side_order(names[1])==[2,1]
    assert checked(0)['source']!=checked(1)['source']
    assert checked(0)['svg']!=checked(1)['svg']


def test_multiple_reader_never_calls_the_writer(monkeypatch):
    context,_=fixture();row=checked(0)
    def forbidden(*args,**kwargs):raise AssertionError('Reader must not regenerate the source')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    assert decode(list(reversed(from_svg(row['svg']))),lexicon=LexicalContext.from_published(context.published()))==row['source']


@pytest.mark.parametrize('extra',[False,True])
def test_second_branch_must_consume_exactly_one_expression(extra):
    context,_=fixture()
    with use_context(context):
        stream=events(cases()[0][2],multiple=True)
        token=stream[0]['extra_sides'][0]
        prefix=[dict(token=token,word=token,side=None,depth=1,path=[2])] if extra else []
        stream[0]['extra_sides'][0]=prefix+[dict(token='not',side=None,depth=1,path=[2])]
        drawing=compile_stream(stream,contacts=False)
    with pytest.raises(ValueError,match='exactly one complete expression|Incomplete visible expression'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=LexicalContext.from_published(context.published()))


def test_three_branches_are_read_without_a_two_branch_limit():
    assert checked(len(cases())-1)['maximum_sides']==3
