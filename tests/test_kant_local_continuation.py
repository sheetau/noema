import pytest

from scripts.check_kant_expression_branches import fixture,cases
from scripts.kant_public_fragment import compile_statement,decode
from scripts.kant_lexical_context import LexicalContext
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.kant_readable_flow import route
from scripts.balanced_circle_script import SMALL,circle,line,_on_segment


def test_a_side_expression_can_extend_beyond_the_main_flow(monkeypatch):
    context,_=fixture();source=cases()[0][2]
    drawing=compile_statement(source,lexicon=context,contacts=False)
    assert drawing['layout']=='interleaved'
    shapes=from_svg(to_svg(drawing['shapes']))
    flow=decompose_flow(read_geometry(shapes),terminal_words=True,branch_seams=True,
        large_branches=True,local_continuation=True)
    x=lambda i:flow['nuclei'][i]['center'][0]
    assert max(x(i) for chain in flow['side'] for i in chain)>max(map(x,flow['main']))
    def forbidden(*args,**kwargs):raise AssertionError('The reader must not consult the writer')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    reader=LexicalContext.from_published(context.published())
    assert decode(list(reversed(shapes)),lexicon=reader)==source


def test_equal_first_nucleus_positions_do_not_infer_order_from_tail_length():
    # Flow-layer diagnostic: two first nuclei have the same x; one tail is
    # longer. The local ordering rule must reject rather than use that tail.
    centers=[(0,32),(100,0),(100,64),(250,64)]
    geometry=dict(circles=[dict(center=list(c),size='medium',component=0) for c in centers],
        relations=[],visible_components=1,
        vertices=[dict(centers=[i],rims=[]) for i in range(4)],edges=[(0,1),(0,2),(2,3)])
    with pytest.raises(ValueError,match='Ambiguous continuation'):
        decompose_flow(geometry,terminal_words=True,local_continuation=True)


def test_separate_connector_does_not_rejoin_existing_line():
    a=dict(x=0.,y=0.,radius=SMALL);b=dict(x=200.,y=0.,radius=SMALL)
    circles=[circle(0,0,SMALL),circle(200,0,SMALL)]
    old=line((60,0),(140,0))
    ordinary=route(a,b,circles,obstacles=[old],detours=True)
    separate=route(a,b,circles,obstacles=[old],detours=True,separate=True)
    assert ordinary and separate and ordinary[0]!=separate[0]
    assert not any(_on_segment(point,s) for point in ((60,0),(140,0)) for s in separate[1])


@pytest.mark.parametrize('old',[
    ((60.,0.),(140.,0.)),((0.,0.),(0.,32.)),((200.,0.),(200.,32.)),
    ((60.,0.),(60.,32.)),((80.,-20.),(120.,20.)),((60.,32.),(140.,32.)),
    ((60.,.001),(140.,.001)),((60.,.1),(140.,.1)),
])
def test_early_rejoin_rejection_matches_the_original_complete_scan(old):
    import math
    from scripts.kant_readable_flow import joins_away_from_ends
    from scripts.balanced_circle_script import EPS
    segments=[line((0.,0.),(200.,0.))];obstacles=[line(*old)];ends=((0.,0.),(200.,0.))
    contacts=[]
    for segment in segments:
        for previous in obstacles:
            contacts.extend(point for point in ((segment['x1'],segment['y1']),(segment['x2'],segment['y2'])) if _on_segment(point,previous))
            contacts.extend(point for point in ((previous['x1'],previous['y1']),(previous['x2'],previous['y2'])) if _on_segment(point,segment))
    expected=any(all(math.dist(point,end)>EPS for end in ends) for point in contacts)
    assert joins_away_from_ends(segments,obstacles,ends)==expected
