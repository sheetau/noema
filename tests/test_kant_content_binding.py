import math
import pytest
from scripts.check_kant_content_binding import cases,checked,content,evaluate,situation
from scripts.check_visible_syntax import call,variable,quote,logic
from scripts.kant_public_fragment import compile_statement,decode,forms,events
from scripts.visible_syntax_geometry import from_svg,to_svg
from scripts.balanced_circle_script import LARGE,SMALL,PITCH


@pytest.mark.parametrize('index',range(len(cases())))
def test_content_scope_and_type_survive_actual_geometry(index):checked(index)


def test_outer_and_inner_situations_keep_their_argument_order():
    a,b=checked(1),checked(2)
    assert a['source']!=b['source'] and a['svg']!=b['svg']


def test_content_uses_implicit_situation_type_and_legal_lower_right_pair():
    stream=events(cases()[0][2]);i=next(i for i,e in enumerate(stream) if e['token']=='content')
    assert stream[i+1]['token']=='equal'
    small,large=sorted((s for s in forms('content')[0]['shapes'] if s['kind']=='circle'),key=lambda s:s['r'])
    assert (small['r'],large['r'])==(SMALL,LARGE)
    assert small['x']>large['x'] and small['y']-large['y']==PITCH
    assert math.isclose(math.dist((small['x'],small['y']),(large['x'],large['y'])),LARGE)


@pytest.mark.parametrize('fault',['wrong-body-type','wrong-variable-type','quote-capture','sibling-capture','reversed-evaluation'])
def test_content_rejects_invalid_body_scope_and_evaluation(fault):
    v=variable;book=call('book')
    if fault=='wrong-body-type':body=situation('s',evaluate(content('t',book),v('s')))
    elif fault=='wrong-variable-type':body=situation('s',evaluate(content('t',call('red',v('t'))),v('s')))
    elif fault=='quote-capture':body=situation('s',logic('equal',quote(content('t',logic('equal',v('t'),v('s')))),quote(content('t',logic('equal',v('t'),v('s'))))))
    elif fault=='sibling-capture':body=logic('equal',content('s',logic('equal',v('s'),v('s'))),content('t',logic('equal',v('s'),v('t'))))
    else:body=situation('s',evaluate(v('s'),content('t',logic('equal',v('t'),v('t')))))
    with pytest.raises(ValueError):compile_statement(dict(kind='assert',body=body),multiple=True)


def test_visible_nontruth_content_body_is_rejected_by_reader(monkeypatch):
    # Content/book is valid geometry but cannot serve as a truth-valued body.
    stream=[dict(token=t,side=None,depth=i,path=[i]) for i,t in enumerate(['content',call('book')['symbol']])]
    monkeypatch.setattr('scripts.kant_public_fragment.events',lambda *args,**kwargs:stream)
    drawing=compile_statement(None,silent=False)
    with pytest.raises(ValueError,match='Content body must have truth sort'):
        decode(from_svg(to_svg(drawing['shapes'])))


def test_reader_has_no_source_writer_or_element_order_oracle(monkeypatch):
    row=checked(12)
    def forbidden(*args,**kwargs):raise AssertionError('Source writer used for inverse')
    monkeypatch.setattr('scripts.kant_public_fragment.compile_statement',forbidden)
    assert decode(list(reversed(from_svg(row['svg']))))==row['source']
