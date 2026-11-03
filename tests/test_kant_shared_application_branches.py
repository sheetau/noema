import pytest
from scripts.check_kant_shared_application_branches import fixture,cases,checked
from scripts.kant_public_fragment import side_order,shared_slot,events,decode
from scripts.kant_lexical_context import use_context,LexicalContext
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import to_svg,from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_shared_predicates_keep_nonshared_branches_and_exact_syntax(index):
    row=checked(index)
    assert row['multiple_owners']>=1
    assert row['maximum_sides']>=2
    assert row['shared_heads']==(2 if row['key']=='quoted' else 1)
    assert row['branch_limits']==[] and row['unbranched_paths']==[]


def test_supplied_positions_leave_one_unshared_argument_on_the_main_flow():
    context,_,names=fixture()
    with use_context(context):
        assert [shared_slot(n) for n in names]==[0,1,2,2]
        assert [side_order(n,(shared_slot(n),)) for n in names]==[[2,3],[2,3],[1],[1,3,4]]
    assert checked(0)['source']!=checked(1)['source']
    assert checked(0)['svg']!=checked(1)['svg']


@pytest.mark.parametrize('fault',['too-many','missing','trailing'])
def test_shared_predicate_rejects_excess_or_incomplete_branches(fault):
    context,_,_=fixture()
    with use_context(context):
        stream=events(cases()[0][2],multiple=True)
        owner=next(e for e in stream if e.get('extra_sides'))
        if fault=='too-many':owner['extra_sides'].append(owner['side'])
        else:
            token=owner['extra_sides'][0]
            prefix=[dict(token=token,word=token,side=None,depth=2,path=[])] if fault=='trailing' else []
            owner['extra_sides'][0]=prefix+[dict(token='not',side=None,depth=2,path=[])]
        drawing=compile_stream(stream)
    with pytest.raises(ValueError,match='Too many branches on a shared predicate|Incomplete visible expression|exactly one complete expression'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=LexicalContext.from_published(context.published()))
