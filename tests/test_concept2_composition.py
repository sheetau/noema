from copy import deepcopy
import math
import pytest
from scripts import concept2_composition as c
from scripts.concept2_controls import controls,geometry_controls


def dictionary():
    spell={n:[c.old.root_symbol(r)] for n,r in zip(('a','b','p'),('aki','book','home'))}
    return dict(selected_spellings=spell,aliases=[dict(symbol=n,parts=p) for n,p in spell.items()],
                native=dict(declarations=[dict(name=n,result='individual' if n!='p' else 'truth') for n in spell]))


def scope(body):return dict(form='scope',quotation=True,body=body)


def test_scope_restoration_alias_arguments_dots_and_binding_controls():
    examples=controls(dictionary(),'a','b','p')
    assert len(examples)==6
    for case in examples:
        assert c.expand_plan(case['plan'],dictionary())==case['expected']
        assert case['drawing']['metrics']['arcs']>0


def test_dots_reject_unpaired_overwritten_and_third_occurrences():
    define=dict(form='dot-definition',label=0,value=17);use=dict(form='dot-use',label=0)
    for body in ([define],[define,define,use],[define,use,use]):
        with pytest.raises(AssertionError):c.expand_plan(scope(body),dictionary())
    assert c.expand_plan(scope([define,use,define,use]),dictionary())==[17]*4


def test_quotation_cannot_capture_role_or_variable():
    definition=dict(form='role-definition',lane=-1,value=3)
    with pytest.raises(KeyError):
        c.expand_plan(scope([definition,scope(dict(form='role-use',lane=-1))]),dictionary())
    expression=dict(kind='exists',variable='va',sort='individual',body=dict(kind='quote',body=dict(kind='variable',name='va')))
    with pytest.raises(ValueError,match='Unbound'):c.plan_units(scope(expression))


def test_all_legal_eclipse_sector_masks_and_forbidden_cutouts():
    for side in (-1,1):
        forbidden={3,4} if side<0 else {7,0}
        outside=sorted(set(range(8))-forbidden)
        for mask in range(1,64):
            sectors=[x for j,x in enumerate(outside) if mask&(1<<j)]
            for contact in (False,True):c.ink_check(c.eclipse(side,contact,sectors))
    for arc in (c.arc(c.L,150,210),c.arc(c.L,210,510)):
        with pytest.raises(ValueError):c.ink_check([arc,c.circle(c.M,-math.hypot(c.L,c.M))])
    with pytest.raises(ValueError):c.eclipse(-1,True,(3,4))


def test_radius_examples_and_all_dot_keys_survive_svg_ink_readback():
    for _,shapes in geometry_controls():
        c.ink_check(c.from_svg(c.svg(shapes,width=500,height=500)))
    for label in range(256):
        shapes=c.dot_shape(label)
        ink=c.from_svg(c.svg(shapes,width=500,height=500))
        c.ink_check(ink)
        assert sum(s['kind']=='dot' for s in ink)==1
    for side in (-1,1):
        for lane in (-1,1):
            small=c.large_link_shape(side,lane)[-1]
            assert abs(abs(small['x'])-c.L-c.M)<c.EPS


def test_fold_keeps_radius_stubs_and_silent_dot_together():
    drawing=controls(dictionary(),'a','b','p')[2]['drawing']
    for width in (480,650,900):
        rows=c.fold([drawing],width)
        assert len(rows)>1
        assert all(r['width']<=width+c.EPS for r in rows)
        for a,b in zip(rows,rows[1:]):assert a['exit_lanes']==b['entry_lanes']
        assert all(abs(x['length']-c.M)<c.EPS for r in rows for x in r['continuations'])


def test_reject_unsupported_binder_instead_of_losing_type_or_arity():
    for parameters in ([dict(name='va',sort='situation')], [dict(name=x,sort='individual') for x in ('va','vb')]):
        with pytest.raises(ValueError,match='one individual'):
            c.plan_units(scope(dict(kind='lambda',parameters=parameters,body=dict(kind='variable',name='va'))))


def test_open_arc_connections_cannot_turn_at_center_or_draw_diameter():
    for lines in ([c.line((-c.M,0),(0,0)),c.line((0,0),(c.P,-c.P))],
                  [c.line((-c.M,0),(c.M,0))]):
        with pytest.raises(ValueError,match='center'):
            c.ink_check([c.arc(c.M,45,315)]+lines)
    drawing=c.compile_units([c.operator('not'),c.unit('upper',c.role_shape(-1))])
    c.ink_check(drawing['shapes'])
