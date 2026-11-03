from copy import deepcopy
import math
import pytest

from scripts import balanced_circle_script as b
from scripts.kant_geometry_reader import read_geometry,recover_seams
from scripts.check_kant_geometry_reader import (
    observed,allowed_pairs,generator_witnesses,regenerated_kant,rejected_forms,
)


@pytest.mark.parametrize('index',range(40))
def test_original_kant_geometry_without_ast_and_visible_seam_recovery(index):
    assert observed(index)['geometry']['circles']


@pytest.mark.parametrize('radius',[b.MEDIUM,b.LARGE])
@pytest.mark.parametrize('direction',range(8))
def test_every_single_center_direction_is_read(radius,direction):
    n=b.nucleus(0,b.PITCH,radius,None,direction)
    r=read_geometry(n['shapes']);c=r['circles'][0]
    assert c['center_direction']==direction
    assert c['center_kind']==('center_diagonal' if radius==b.LARGE and direction%2 else 'radius')


@pytest.mark.parametrize('direction',[1,3,5,7])
def test_outer_diagonal_is_distinct_from_center_diagonal(direction):
    n=b.nucleus(0,b.PITCH,b.LARGE,None,direction,mode='outer')
    c=read_geometry(n['shapes'])['circles'][0]
    assert c['center_kind']=='center_free'
    assert c['outer_diagonals']==[direction]


@pytest.mark.parametrize('radius',[b.SMALL,b.MEDIUM])
@pytest.mark.parametrize('direction',range(8))
def test_all_eight_center_free_rim_ports(radius,direction):
    x,y=math.cos(direction*math.pi/4),math.sin(direction*math.pi/4)
    r=read_geometry([b.circle(0,b.PITCH,radius),
        b.line((radius*x,b.PITCH+radius*y),((radius+b.MIN_RUN)*x,b.PITCH+(radius+b.MIN_RUN)*y))])
    assert r['circles'][0]['center_kind']=='center_free'
    assert r['circles'][0]['external_ports']==[direction]


@pytest.mark.parametrize('direction',range(8))
def test_external_center_connection_in_all_legal_medium_directions(direction):
    x,y=math.cos(direction*math.pi/4),math.sin(direction*math.pi/4)
    distance=32*math.sqrt(2) if direction%2 else 32 if direction in (2,6) else 80
    start=dict(x=-x*distance,y=b.PITCH-y*distance,radius=b.SMALL)
    end=dict(x=0,y=b.PITCH,radius=b.MEDIUM)
    rings=[b.circle(start['x'],start['y'],b.SMALL),b.circle(0,b.PITCH,b.MEDIUM)]
    _,lines=b.route(start,end,rings,end_center=True)
    geometry=read_geometry(rings+lines)
    c=next(c for c in geometry['circles'] if c['size']=='medium')
    # At vertical M/S tangency, the incoming stroke has exactly radius length.
    # Its connection is visible in the circle relation, not an extra ink mode.
    assert c['center_kind']==('radius' if direction in (2,6) else 'center_external')
    if direction in (2,6):assert geometry['relations'][0]['kind']=='tangent'
    assert c['center_direction']==(direction+4)%8


def test_legally_paired_positions_are_read_including_unemitted_forms():
    pairs=allowed_pairs()
    assert {r['kind'] for r in pairs}=={'concentric','tangent','center_on_rim'}
    assert any(not r['directly_available_in_old_constructor'] for r in pairs)
    assert any(r['rails'][0]!=r['rails'][1] and r['kind']=='center_on_rim' for r in pairs)
    assert any(r['kind']=='concentric' and b.SMALL in r['radii'] for r in pairs)
    for p in pairs:assert read_geometry(p['shapes'])['relations'][0]['kind']==p['kind']


def test_independently_drawn_asymmetric_branch():
    # Three medium circles, a real T junction and one off-axis dependency.
    shapes=[b.circle(0,32,b.MEDIUM),b.circle(150,32,b.MEDIUM),
        b.circle(75,0,b.SMALL),b.line((b.MEDIUM,32),(150-b.MEDIUM,32)),
        b.line((75,32),(75,b.SMALL))]
    r=read_geometry(shapes)
    assert r['visible_components']==1
    assert sum(v['degree']==3 for v in r['vertices'])==1
    assert len(r['circles'])==3


def test_line_element_order_and_subdivision_carry_no_information():
    rows,_,_=generator_witnesses();shapes=rows[2]['drawing']['shapes'];split=[]
    for s in shapes:
        if s['kind']=='circle':split.append(s)
        else:
            a,c=(s['x1'],s['y1']),(s['x2'],s['y2']);m=((a[0]+c[0])/2,(a[1]+c[1])/2)
            split.extend([b.line(c,m),b.line(m,a)])
    assert read_geometry(list(reversed(split)))==read_geometry(shapes)


def test_silent_seams_are_decoded_without_hidden_edges():
    shapes=[b.circle(0,0,b.SMALL),b.circle(32,32,b.MEDIUM),b.circle(32,64,b.SMALL)]
    # The last two circles touch: one component; first-to-next is diagonal.
    r=read_geometry(shapes)
    assert recover_seams(r)==[[[0,0],[32,32]]]


def test_interleaved_silent_components_are_not_guessed():
    # The long line belongs to the lower component; a separate ring sits above.
    shapes=[b.circle(0,32,b.SMALL),b.circle(200,32,b.SMALL),b.circle(100,0,b.SMALL),
        b.line((b.SMALL,32),(200-b.SMALL,32))]
    with pytest.raises(ValueError,match='Interleaved'):recover_seams(read_geometry(shapes))


def test_unaligned_silent_components_are_not_guessed():
    with pytest.raises(ValueError,match='Unaligned'):
        recover_seams(read_geometry([b.circle(0,0,b.SMALL),b.circle(100,32,b.SMALL)]))


def test_previous_draft_forms_fail_the_original_geometry_rules():
    assert set(rejected_forms())=={'small-center-row-number','two-center-directions','three-concentric-circles'}


def test_unknown_fields_and_forbidden_strokes_rejected():
    ring=b.circle(0,32,b.SMALL)
    with pytest.raises(ValueError):read_geometry([dict(ring,source='hidden')])
    with pytest.raises(ValueError,match='center stroke'):
        read_geometry([ring,b.line((0,32),(b.SMALL,32))])
    with pytest.raises(ValueError):
        read_geometry([b.circle(0,32,b.LARGE),b.line((0,32),(b.LARGE/math.sqrt(2),32+b.LARGE/math.sqrt(2)))])
    with pytest.raises(ValueError):
        read_geometry([b.circle(0,32,b.MEDIUM),b.line((0,32),(b.MEDIUM,32)),b.line((0,32),(0,32-b.MEDIUM))])


def test_actual_generator_and_lexical_collision_boundary():
    normal,collision,association=generator_witnesses()
    assert len(normal)==6
    assert collision['left']!=collision['right'] and collision['svg_equal']
    assert association['left']!=association['right']
    assert set(regenerated_kant())=={'native-call','conjunction','quoted-argument','function-argument','evaluation'}
