from copy import deepcopy
import math
import pytest

from scripts.check_kant_quotation_operations import cases,checked,assemble,lift,disquote
from scripts.check_kant_function_application import fixture,ref
from scripts.check_visible_syntax import call,quote,logic,variable,quant
from scripts.kant_public_fragment import compile_statement,decode,events,forms
from scripts.kant_lexical_context import LexicalContext,use_context
from scripts.kant_interleaved_layout import compile_stream
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.balanced_circle_script import LARGE,SMALL,PITCH
from scripts.kant_geometry_rules import geometry_check


@pytest.mark.parametrize('index',range(len(cases())))
def test_quotation_operations_recover_original_native_syntax(index):
    checked(index)


def test_argument_order_and_rank_distinctions_remain_visible():
    left,right=checked(0),checked(1)
    assert left['source']!=right['source'] and left['svg']!=right['svg']
    assert checked(8)['source']['body']['rank']==2
    assert checked(15)['source']['body']['arguments'][0]['rank']==2


@pytest.mark.parametrize('token',['quoted_application','quoted_lift','disquote'])
def test_new_pairs_use_adjacent_rails_and_small_center_on_large_rim(token):
    rings=[s for s in forms(token)[0]['shapes'] if s['kind']=='circle']
    small,large=sorted(rings,key=lambda c:c['r'])
    assert (small['r'],large['r'])==(SMALL,LARGE)
    assert abs(small['y']-large['y'])==PITCH
    assert math.isclose(math.dist((small['x'],small['y']),(large['x'],large['y'])),LARGE)


@pytest.mark.parametrize('fault',['bare-function','non-function-description','non-description-lift','non-description-disquote','missing','extra'])
def test_malformed_quotation_operations_are_rejected_from_ink(fault,monkeypatch):
    context,_=fixture()
    with use_context(context):
        if fault in ('non-description-lift','non-description-disquote'):
            body=(lift if fault.endswith('lift') else disquote)(call('book'))
        else:
            f=ref('red') if fault=='bare-function' else quote(call('book')) if fault=='non-function-description' else quote(ref('above'))
            args=[quote(call('aki'))] if fault=='missing' else [quote(call(n)) for n in ('aki','nao','book')] if fault=='extra' else [quote(call('book'))]
            body=assemble(f,*args)
        # Bypass only the writer's native source check, to probe the reader.
        with monkeypatch.context() as writer_only:
            writer_only.setattr('scripts.kant_public_fragment.validate_native',lambda statement:statement)
            stream=events(dict(kind='assert',body=body),branch=fault=='extra',multiple=True)
        drawing=compile_stream(stream)
    with pytest.raises(ValueError,match='requires a description type|requires a function type|Incomplete visible expression|Too many branches'):
        decode(from_svg(to_svg(drawing['shapes'])),lexicon=LexicalContext.from_published(context.published()))


@pytest.mark.parametrize('fault',['same-rank','wrong-annotation','capture','wrong-sort'])
def test_source_rank_scope_and_sort_rejections(fault):
    context,_=fixture();book=call('book')
    if fault=='same-rank':
        term=quote(disquote(quote(call('red',book),1)),1);body=logic('equal',term,term)
    elif fault=='wrong-annotation':body={**disquote(quote(call('red',book),2)),'rank':1}
    elif fault=='capture':body=quant('forall','x',disquote(assemble(quote(ref('red')),quote(variable('x')))))
    else:body=disquote(assemble(quote(ref('red')),quote(call('red',book))))
    with pytest.raises(ValueError):compile_statement(dict(kind='assert',body=body),lexicon=context,multiple=True)


def test_reader_needs_no_writer_or_authored_segment_boundaries(monkeypatch):
    row=checked(0);context,_=fixture()
    def forbidden(*args,**kwargs):raise AssertionError('Writer used as inverse oracle')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    shapes=[]
    for s in reversed(from_svg(row['svg'])):
        if s['kind']=='circle':shapes.append(deepcopy(s))
        else:
            x,y=(s['x1']+s['x2'])/2,(s['y1']+s['y2'])/2
            shapes.extend([dict(kind='line',x1=s['x2'],y1=s['y2'],x2=x,y2=y),dict(kind='line',x1=x,y1=y,x2=s['x1'],y2=s['y1'])])
    assert decode(shapes,lexicon=LexicalContext.from_published(context.published()))==row['source']


def test_segmentation_cannot_disguise_a_four_way_crossing_as_endpoints():
    def line(a,b):return dict(kind='line',x1=a[0],y1=a[1],x2=b[0],y2=b[1])
    center=(32,32)
    split=[line(p,center) for p in ((0,32),(64,32),(32,0),(32,64))]
    joined=[line((0,32),(64,32)),line((32,0),(32,64))]
    for shapes in (split,joined):
        with pytest.raises(ValueError,match='Unintended crossing'):
            geometry_check(shapes,[])
    # A three-arm branch has an actual endpoint on one of the two axes.
    assert geometry_check(split[:3],[])
