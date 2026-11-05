from copy import deepcopy
from itertools import product,combinations
import math
import xml.etree.ElementTree as ET
import pytest
from scripts import concept2_geometry_v5 as g,concept2_composition as v2
from scripts.concept2_codec_v5 import Codec
from scripts.concept2_controls import controls


@pytest.fixture(scope='module')
def codec():
    spell={n:list(map(v2.old.root_symbol,parts)) for n,parts in {
        'a':['aki'],'b':['book'],'p':['home'],'q':['home','home'],'f':['round','round'],'r':['home','aki'],'z':['above','above','above']}.items()}
    decl=[dict(name=n,result='truth' if n in ('p','q','r') else 'individual',
               parameters=[dict(name='v'+x,sort='individual') for x in ('a','b')[:{'p':1,'q':2,'f':2}.get(n,0)]]) for n in spell]
    return Codec(dict(selected_spellings=spell,aliases=[dict(symbol=n,parts=p) for n,p in spell.items()],native=dict(declarations=decl)))


def call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
def join(kind,a,b):return dict(kind=kind,arguments=[a,b])
def assertion(body):return dict(kind='assert',body=body)


def render(codec,statement):
    plan=v2.make_plan(statement,codec.dictionary,sharing=False)['plan'];tokens=codec.encode(plan)
    drawing=g.layout(codec.units(tokens))[0]
    return tokens,drawing,v2.svg(drawing['shapes'])


def test_eclipse_keeps_inner_arc_and_pairs_only_outer_wings():
    beta=math.degrees(math.atan2(g.M,g.L))
    for side in (-1,1):
        phi=180 if side<0 else 0;excluded={3,4} if side<0 else {7,0};outside=sorted(set(range(8))-excluded)
        for mask in range(1,64):
            sectors=[s for i,s in enumerate(outside) if mask&(1<<i)]
            for contact in (False,True):
                shapes=g.eclipse(side,contact,sectors);g.ink_check(shapes)
                large=[s for s in shapes if s['r']==g.L]
                assert all(any(g.on_arc(s,phi+a) for s in large) for a in (-beta+.01,0,beta-.01))
                assert all(any(g.on_arc(s,phi+a) for s in large)==contact for a in (-(45+beta)/2,(45+beta)/2))
    with pytest.raises(ValueError,match='inside medium'):g.ink_check(v2.eclipse(-1,False,(0,1)))


def test_small_circle_interior_is_forbidden_even_without_center_hit():
    for stroke in (g.line((-20,8),(20,8)),g.line((-20,0),(0,0)),g.line((0,0),(10,0))):
        with pytest.raises(ValueError):g.ink_check([g.circle(g.S),stroke])
    g.ink_check([g.circle(g.S),g.line((-20,0),(-g.S,0))])


def test_any_positive_side_arc_promotes_medium_large_but_not_fourth_circle():
    cases=[([g.arc(g.M,45,315),g.circle(g.S)],g.M),
           ([g.arc(g.M,90,270),g.circle(g.S)],g.S),
           ([g.arc(g.L,90,270),g.arc(g.M,45,315),g.circle(g.S)],g.M),
           ([g.arc(g.L,45,315),g.circle(g.M),g.circle(g.S)],g.L),
           ([g.arc(g.F,135,225),g.arc(g.M,90,270),g.circle(g.S)],g.S)]
    for shapes,expected in cases:assert g.port(shapes,1)[1][0]==pytest.approx(expected)
    assert g.port([g.arc(g.M,45,270),g.circle(g.S)],1)[1][0]==pytest.approx(g.M)
    for radius in (g.M,g.L):
        # Even a short arc in this half promotes the full-circle endpoint.
        assert g.port([g.arc(radius,80,100),g.circle(g.S)],1)[1][0]==pytest.approx(radius)
        assert g.port([g.arc(radius,260,280),g.circle(g.S)],-1)[1][0]==pytest.approx(-radius)


def test_radial_free_ends_stop_at_circumference_and_connections_are_exempt():
    for angle in (0,45,90,135,180,225,270,315):
        a=math.radians(angle);p=lambda r:(r*math.cos(a),r*math.sin(a))
        # Horizontal examples stay on the center rail.
        g.ink_check([g.circle(g.M),g.line(p(g.M),p(g.F))])
        with pytest.raises(ValueError,match='fourth circle'):
            g.ink_check([g.circle(g.M),g.line(p(g.M),p(g.F+1))])
        with pytest.raises(ValueError,match='fourth circle'):
            g.ink_check([g.circle(g.M),g.line(p(g.M),p(g.L)),g.line(p(g.L),p(g.F+1))])
    g.ink_check([g.circle(g.L),g.circle(g.S,g.L+g.M+g.S),g.line((g.L,0),(g.L+g.M,0))])


def test_branch_columns_and_cutout_selection(codec):
    shapes=g.branch_shape((-1,0,1));small=[s for s in shapes if s['kind']=='arc' and s['r']==g.S]
    centers=[(s['x'],s['y']) for s in small];spacing=2*g.S+g.M
    for i,lane in enumerate((-1,0,1)):
        assert ((i+1)*spacing,0) in centers
        assert ((i+1)*spacing,(-1 if i%2==0 else 1)*g.P) in centers
    for lanes in ((-1,0),(-1,1),(0,1),(-1,0,1)):
        g.ink_check(g.selection_shape(lanes))
        assert ('select',*lanes) in codec.forms


def test_dots_start_at_medium_and_masks_remain_distinct(codec):
    assert len({g.dot_mask(i) for i in range(256)})==256
    shapes=g.dot_shape(0)
    assert any(s['kind']=='arc' and s['r']==g.M for s in shapes)
    assert not any(s['kind']=='arc' and s['r']==g.L for s in shapes)
    assert ('dot-bare',153) in codec.forms and ('dot-bare',0) not in codec.forms
    assert sum(s['b']-s['a'] for s in shapes if s['kind']=='arc' and s['r']==g.M)<360
    for label in range(256):
        if label!=153:assert not any(s['kind']=='arc' and s['r']==g.L for s in g.dot_shape(label))


def test_svg_roundtrip_preserves_argument_order_and_prefix_word_boundary(codec):
    a,b=call('a'),call('b')
    for body in (call('p',a),call('q',a,b),call('q',b,a),call('p',call('z'))):
        expected=assertion(body);tokens,drawing,svg=render(codec,expected)
        assert codec.read_svg(svg)['native']==expected
    ts,_,_=render(codec,assertion(call('p',a)))
    assert ('word-end',) in ts
    # Deleting a meaningful stop can produce another valid word; it must never
    # silently retain the original p(a) reading.
    assert codec.parse([t for t in ts if t!=('word-end',)])==assertion(call('r'))


def test_repeat_preserves_count_and_never_compresses_small_circle(codec):
    statement=assertion(call('p',call('z')));tokens,_,svg=render(codec,statement)
    assert ('repeat',3) in tokens
    assert tokens[-1]==('word-end',)
    assert codec.read_svg(svg)['native']==statement
    tokens,_,svg=render(codec,assertion(call('q',call('a'),call('a'))))
    assert tokens[-2:]==[('root','aki'),('root','aki')]
    assert codec.read_svg(svg)['native']['body']['arguments']==[call('a'),call('a')]


def test_svg_order_ids_line_and_arc_segmentation_do_not_carry_syntax(codec):
    expected=assertion(call('p',call('z')));_,drawing,_=render(codec,expected)
    split=[]
    for s in drawing['shapes']:
        if s['kind']=='line':
            mid=((s['x1']+s['x2'])/2,(s['y1']+s['y2'])/2)
            split += [g.line((s['x1'],s['y1']),mid),g.line(mid,(s['x2'],s['y2']))]
        elif s['kind']=='arc':
            mid=(s['a']+s['b'])/2
            split += [g.arc(s['r'],s['a'],mid,s['x'],s['y']),g.arc(s['r'],mid,s['b'],s['x'],s['y'])]
        else:split.append(s)
    raw=v2.svg(split);root=ET.fromstring(raw);group=list(root)[0]
    group[:]=list(reversed(list(group)))
    for i,e in enumerate(group):e.set('id',f'unrelated-{i}');e.set('data-native','wrong')
    assert codec.read_svg(ET.tostring(root,encoding='unicode'))['native']==expected


def test_reject_unknown_ink_missing_mark_and_wrong_radius_connection(codec):
    expected=assertion(call('p',call('a')));tokens,drawing,svg=render(codec,expected)
    bad=deepcopy(drawing['shapes']);bad.append(g.circle(11,1000))
    with pytest.raises(ValueError):codec.read_svg(v2.svg(bad))
    bad=deepcopy(drawing['shapes'])
    route=next(s for s in bad if s['kind']=='line' and abs(s['y1']-s['y2'])<g.EPS)
    route['x2']-=2
    with pytest.raises(ValueError):codec.read_svg(v2.svg(bad))


def test_scope_dot_alias_and_hole_controls_read_from_svg(codec):
    for ex in controls(codec.dictionary,'a','b','p'):
        tokens=codec.encode(ex['plan']);drawing=g.layout(codec.units(tokens))[0]
        assert codec.read_svg(v2.svg(drawing['shapes']))['native']==ex['expected'],ex['title']


def test_real_fork_recovers_shared_arguments_in_trunk_order(codec):
    def w(name):return dict(kind='call',symbol=dict(form='word',parts=codec.dictionary['selected_spellings'][name]),arguments=[])
    def define(lane,name):return dict(form='role-definition',lane=lane,value=w(name))
    def use(lane):return dict(form='role-use',lane=lane)
    body=join('and',join('equal',define(-1,'a'),define(1,'b')),
              dict(kind='call',symbol=dict(form='word',parts=codec.dictionary['selected_spellings']['q']),arguments=[use(1),use(-1)]))
    plan=dict(form='scope',quotation=True,body=assertion(body));expected=v2.expand_plan(plan,codec.dictionary)
    tokens=codec.encode(plan);assert ('merge',1,-1) in tokens
    drawing=g.layout(codec.units(tokens))[0]
    assert codec.read_svg(v2.svg(drawing['shapes']))['native']==expected


def test_all_cutout_selections_and_large_dot_fallback_read_from_svg(codec):
    def w(name):return dict(kind='call',symbol=dict(form='word',parts=codec.dictionary['selected_spellings'][name]),arguments=[])
    definitions=[dict(kind='equal',arguments=[dict(form='role-definition',lane=lane,value=w('a' if lane<1 else 'b')),w('a')]) for lane in (-1,0,1)]
    for lanes in ((-1,0),(-1,1),(0,1),(-1,0,1)):
        uses=[dict(form='role-use',lane=lane) for lane in lanes]
        # Test the vector recognizer independently of declaration arity.
        drawing=g.layout(codec.units([('select',*lanes)]))[0]
        assert codec.read_svg(v2.svg(drawing['shapes']),fragment=True)['tokens']==[('select',*lanes)]
        if len(lanes)==2:
            body=dict(kind='call',symbol=dict(form='word',parts=codec.dictionary['selected_spellings']['q']),arguments=uses)
            for definition in reversed(definitions):body=join('and',definition,body)
            plan=dict(form='scope',quotation=True,body=assertion(body));tokens=codec.encode(plan)
            assert ('select-directed',*lanes) in tokens
            drawing=g.layout(codec.units(tokens))[0]
            assert codec.read_svg(v2.svg(drawing['shapes']))['native']==v2.expand_plan(plan,codec.dictionary)
    for label in (0,1,129,153,255):
        body=join('equal',dict(form='dot-definition',label=label,value=w('a')),dict(form='dot-use',label=label))
        plan=dict(form='scope',quotation=True,body=assertion(body));drawing=g.layout(codec.units(codec.encode(plan)))[0]
        assert codec.read_svg(v2.svg(drawing['shapes']))['native']==v2.expand_plan(plan,codec.dictionary)


def test_merge_orders_and_directed_selection_are_read_from_ink(codec):
    for n in (2,3):
        for lanes in product((-1,0,1),repeat=n):
            token=('merge',*lanes);drawing=g.layout(codec.units([token]))[0]
            assert codec.read_svg(v2.svg(drawing['shapes']),fragment=True)['tokens']==[token]
        for lanes in combinations((-1,0,1),n):
            for i in range(n):
                order=lanes[i:]+lanes[:i];token=('select-directed',*order)
                drawing=g.layout(codec.units([token]))[0]
                assert codec.read_svg(v2.svg(drawing['shapes']),fragment=True)['tokens']==[token]


def test_every_dot_arc_choice_decodes_without_forcing_large_circle(codec):
    for label in range(256):
        token=('dot',label);drawing=g.layout(codec.units([token]))[0]
        assert codec.read_svg(v2.svg(drawing['shapes']),fragment=True)['tokens']==[token]


def test_merge_composes_repeated_arguments_results_quotes_and_binders(codec):
    from scripts.build_concept2_confluence import confluence_controls
    for ex in confluence_controls(codec.dictionary,'a','b','f'):
        tokens=codec.encode(ex['plan']);drawing=g.layout(codec.units(tokens))[0]
        assert any(t[0]=='merge' for t in tokens)
        assert codec.read_svg(v2.svg(drawing['shapes']))['native']==ex['expected']
    with pytest.raises((ValueError,KeyError)):codec.parse([('root','home'),('merge',1,-1)])


def test_folded_page_is_decoded_without_statement_or_row_metadata(codec):
    statements=[assertion(call('p',call('z'))),assertion(call('q',call('b'),call('a')))]
    drawings=[render(codec,s)[1] for s in statements]
    for width in (340,900):
        rows=g.fold(drawings,width);shapes=[]
        for i,row in enumerate(rows):shapes.extend(g.move(row['shapes'],60,80+i*170))
        result=codec.read_page(v2.svg(shapes,width=1100,height=170*len(rows)+100))
        assert result['statements']==statements


def test_unpaired_dots_and_out_of_scope_values_are_rejected(codec):
    with pytest.raises((KeyError,ValueError)):codec.parse([('role-use',-1)])
    with pytest.raises(ValueError,match='Unpaired'):
        codec.parse([('dot',0),('root','aki')])


def test_visible_ink_only_and_every_registered_form_obeys_geometry(codec):
    for form in codec.forms.values():g.ink_check(form['shapes'])
    _,_,svg=render(codec,assertion(call('p',call('a'))))
    root=ET.fromstring(svg);list(root)[0].set('opacity','0')
    with pytest.raises(ValueError,match='hidden'):codec.read_svg(ET.tostring(root,encoding='unicode'))
