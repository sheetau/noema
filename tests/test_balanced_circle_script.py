from copy import deepcopy
from itertools import combinations, permutations
from collections import Counter
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from noema.constructed import parse
from scripts.balanced_circle_script import (
    compile_expression, geometry_check, pack_lines, restore, expanded_tree,
    SMALL, MEDIUM, LARGE, MIN_RUN, MIN_GAP, circle, line, near, EPS, events, display_tree,
    nucleus, spacing_check, route,
)
from scripts.proof_balanced_circle_script import specimens, OUT, KANT, SCALE, GUIDE, diagonal_witnesses, layout_comparison


def visible(c):
    return json.dumps(c['shapes'],sort_keys=True)


def test_entire_syntax_and_every_occurrence_survive_without_repeated_parent_ports():
    for entry in specimens()['entries']:
        c=entry['compiled']
        assert restore(expanded_tree(c['tree']))==c['source']
        paths=[]
        def walk(n,p=()):
            paths.append(list(p))
            for i,ch in enumerate(n['children']):walk(ch['node'],p+(i,))
        walk(c['tree'])
        if c['tree']['tag']=='assert':paths.remove([])
        actual=[g['path'] for g in c['groups']]+[s['path'] for g in c['groups'] for s in g['satellites']]
        actual += [p for g in c['groups'] for p in g['fused_paths']]
        actual += [p for g in c['groups'] for s in g['satellites'] for p in s['fused_paths']]
        assert sorted(actual)==sorted(paths)


def test_kant_uses_the_actual_native_assertions_quotes_and_quantification():
    doc=parse(Path(KANT).read_text(encoding='utf-8'))
    definitions={d['name']:d for d in doc['declarations']}
    for entry in specimens()['entries'][6:8]:
        assert entry['original_assertion'] in doc['statements']
        assert entry['compiled']['source']['body']==definitions[entry['expanded_definition']]['body']
    tags={k for k,_ in specimens()['entries'][7]['compiled']['dictionary']}
    assert {'quote','function_ref'}<=tags
    tags={k for k,_ in specimens()['entries'][8]['compiled']['dictionary']}
    assert {'content','forall','exists','variable'}<=tags


def test_new_geometry_is_checked_on_entire_sentences_not_independent_tiles():
    for entry in specimens()['entries']:
        c=entry['compiled']
        assert geometry_check(c['shapes'],c['paths'],c['invisible'])
        assert len(c['invisible'])<=max(1,len(c['groups'])//12)


def _connected_components(c):
    shapes=c['shapes']; parent=list(range(len(shapes)))
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    def join(i,j):parent[root(i)]=root(j)
    def ends(s):return (s['x1'],s['y1']),(s['x2'],s['y2'])
    def cross(a,b):return a[0]*b[1]-a[1]*b[0]
    def sub(a,b):return (a[0]-b[0],a[1]-b[1])
    def segments(a,b):
        p,q=ends(a);r,s=ends(b);u=sub(q,p);v=sub(s,r);d=cross(u,v)
        if abs(d)>EPS:
            return -EPS<=cross(sub(r,p),v)/d<=1+EPS and -EPS<=cross(sub(r,p),u)/d<=1+EPS
        return any(abs(math.dist(p,z)+math.dist(z,q)-math.dist(p,q))<EPS for z in (r,s)) or any(abs(math.dist(r,z)+math.dist(z,s)-math.dist(r,s))<EPS for z in (p,q))
    for i,a in enumerate(shapes):
        for j in range(i):
            b=shapes[j]
            if a['kind']==b['kind']=='circle':
                distance=math.hypot(a['x']-b['x'],a['y']-b['y'])
                connected=abs(a['r']-b['r'])-EPS<=distance<=a['r']+b['r']+EPS
            elif a['kind']==b['kind']=='line':connected=segments(a,b)
            else:
                ring,stroke=(a,b) if a['kind']=='circle' else (b,a)
                p,q=ends(stroke);v=sub(q,p);center=(ring['x'],ring['y'])
                t=max(0,min(1,sum(x*y for x,y in zip(sub(center,p),v))/sum(x*x for x in v)))
                nearest=math.dist(center,(p[0]+t*v[0],p[1]+t*v[1]))
                connected=nearest<=ring['r']+EPS and max(math.dist(center,p),math.dist(center,q))>=ring['r']-EPS
            if connected:join(i,j)
    for edge in c['invisible']:
        indices=[]
        for p in edge['centers']:
            indices.append(next(i for i,s in enumerate(shapes) if s['kind']=='circle' and near(s['x'],p[0]) and near(s['y'],p[1])))
        join(*indices)
    return len({root(i) for i in range(len(shapes))})


def test_every_sentence_is_connected_including_nested_rings_and_silent_edges():
    for entry in specimens()['entries']:
        assert _connected_components(entry['compiled'])==1,entry['label']


def test_small_centers_and_multiple_center_axes_are_rejected_but_one_axis_is_legal():
    with pytest.raises(ValueError,match='Small circle'):
        geometry_check([circle(0,32,SMALL),line((0,32),(SMALL,32))],[])
    with pytest.raises(ValueError,match='multiple stroke'):
        geometry_check([circle(0,32,MEDIUM),line((0,32),(MEDIUM,32)),line((0,32),(0,32+MEDIUM))],[])
    assert geometry_check([circle(0,32,MEDIUM),line((0,32),(MEDIUM,32))],[])
    with pytest.raises(ValueError,match='Diameter'):
        geometry_check([circle(0,32,MEDIUM),line((-MEDIUM,32),(MEDIUM,32))],[])
    with pytest.raises(ValueError,match='Diameter'):
        geometry_check([circle(0,32,MEDIUM),line((-MEDIUM,32),(0,32)),line((0,32),(MEDIUM,32))],[])
    rings=[circle(0,32,MEDIUM),circle(0,32,SMALL)]
    with pytest.raises(ValueError,match='inside circle'):
        geometry_check(rings+[line((-MEDIUM,32),(-SMALL,32))],[])
    assert geometry_check([circle(0,32,LARGE),circle(0,32,MEDIUM),line((0,32),(LARGE,32))],[])
    with pytest.raises(ValueError,match='inside circle'):
        geometry_check([circle(0,32,MEDIUM),line((-MEDIUM,32),(-7,32))],[])


def test_prior_geometric_constraints_and_straight_invisible_connections_remain_enforced():
    with pytest.raises(ValueError,match='partner'):
        geometry_check([circle(0,32,r) for r in (SMALL,MEDIUM,LARGE)],[])
    with pytest.raises(ValueError,match='center stroke'):
        geometry_check([circle(0,32,LARGE)],[])
    rings=[circle(0,0,MEDIUM),circle(32,32,MEDIUM)]
    with pytest.raises(ValueError,match='nonradial'):
        geometry_check(rings+[line((0,32),(32,0))],[])
    lines=[line((0,0),(20,0)),line((20,0),(20,32)),line((20,32),(52,32))]
    with pytest.raises(ValueError,match='right-angle'):geometry_check(lines,[])
    rings=[circle(0,0,SMALL),circle(60,32,SMALL)]
    with pytest.raises(ValueError,match='straight allowed'):
        geometry_check(rings,[],[dict(centers=[(0,0),(60,32)])])
    diagonal=line((0,32),(LARGE,32+LARGE))
    assert geometry_check([circle(0,32,LARGE),diagonal],[])
    with pytest.raises(ValueError,match='terminate freely|too close'):
        geometry_check([circle(0,32,LARGE),diagonal,line((LARGE,32+LARGE),(LARGE,80))],[])
    with pytest.raises(ValueError,match='terminate freely'):
        geometry_check([circle(0,32,LARGE),line((0,32),(LARGE+5,37+LARGE))],[])


def test_context_changes_form_and_long_passages_balance_without_fixed_central_roots():
    entries=specimens()['entries']
    long=entries[7]['compiled']
    assert abs(long['normalized_moment'])<.1
    assert {g['y'] for g in long['groups']}=={0,32,64}
    assert sum(bool(g['satellites']) for e in entries for g in e['compiled']['groups'])>=10
    forms={}
    for g in long['groups']:forms.setdefault(g['code'],set()).add((g['y'],g['pair'],bool(g['satellites'])))
    assert sum(len(v)>1 for v in forms.values())>=3
    # The brief weather sentence still articulates predicate and place.
    assert len(entries[0]['compiled']['groups'])==2


def test_argument_and_operand_order_are_visible_but_alpha_renaming_is_not():
    source=specimens()['entries'][2]['compiled'];changed=deepcopy(source['source'])
    args=changed['body']['arguments'];args[0],args[2]=args[2],args[0]
    assert visible(source)!=visible(compile_expression(changed,reference_order=source['reference_order']))
    source=specimens()['entries'][9]['compiled'];changed=deepcopy(source['source'])
    changed['arguments'][0]['arguments'].reverse()
    assert visible(source)!=visible(compile_expression(changed,reference_order=source['reference_order']))
    source=specimens()['entries'][2]['compiled']
    mapping={'aki':'person1','nao':'person2','give':'transfer','book':'object'}
    def rename(value):
        if isinstance(value,dict):return {k:(mapping.get(v,v) if k=='symbol' else rename(v)) for k,v in value.items()}
        if isinstance(value,list):return [rename(v) for v in value]
        return value
    reference_order={mapping.get(k,k):v for k,v in source['reference_order'].items()}
    assert visible(source)==visible(compile_expression(rename(source['source']),reference_order=reference_order))
    with pytest.raises(ValueError,match='registry'):compile_expression(source['source'])


def test_wrapping_preserves_every_circle_and_the_total_visible_stroke_length():
    c=specimens()['entries'][7]['compiled']
    for width in (500,806,1660):
        rows=pack_lines(c,width,SCALE)
        rings=lambda shapes:sum(s['kind']=='circle' for s in shapes)
        length=lambda shapes:sum(math.hypot(s['x2']-s['x1'],s['y2']-s['y1']) for s in shapes if s['kind']=='line')
        assert sum(rings(r['shapes']) for r in rows)==rings(c['shapes'])
        assert sum(length(r['shapes']) for r in rows)==pytest.approx(length(c['shapes']))
        assert all(-EPS<=s['x']-s['r'] and s['x']+s['r']<=width/SCALE+EPS for r in rows for s in r['shapes'] if s['kind']=='circle')


def test_one_sheet_retains_readable_kant_ink_and_all_requested_examples():
    data=json.loads((OUT/'specimens.json').read_text(encoding='utf-8'))
    image=Image.open(OUT/'overview.png').convert('RGB')
    assert image.size==(data['sheet']['width'],data['sheet']['height'])
    assert data['sheet']['scale']==SCALE<.6 and data['sheet']['guide_color']==GUIDE
    assert [e['section'] for e in data['entries']].count('normal')==6
    for e in data['entries'][6:9]:
        d=e['display'];x,y=d['x'],d['y']
        crop=image.crop((x,y-12,x+d['width'],y+(d['rows']-1)*66+44)).convert('L')
        assert sum(crop.histogram()[:110])>200
    svg=ET.fromstring((OUT/'overview.svg').read_text(encoding='utf-8'))
    meta=json.loads(svg.find('{http://www.w3.org/2000/svg}metadata').text)
    assert meta['entries'][7]['compiled']['source']==data['entries'][7]['compiled']['source']


def test_minimum_radial_run_including_separately_stored_straight_segments():
    ring=circle(0,32,MEDIUM)
    x=MEDIUM+MIN_RUN
    assert geometry_check([ring,line((MEDIUM,32),(x,32)),line((x,32),(x+32,64))],[])
    x=MEDIUM+MIN_RUN-1
    bad=[ring,line((MEDIUM,32),(MEDIUM+4,32)),line((MEDIUM+4,32),(x,32)),line((x,32),(x+32,64))]
    with pytest.raises(ValueError,match='too close'):geometry_check(bad,[])
    # An intersection in the middle of two separately stored lines also counts
    # as a branch, even if neither input segment ended at the junction.
    bad=[ring,line((MEDIUM,32),(MEDIUM+40,32)),line((x,0),(x,64))]
    with pytest.raises(ValueError,match='too close'):geometry_check(bad,[])


def test_shared_subject_fusion_preserves_scope_and_every_original_occurrence():
    c=specimens()['entries'][3]['compiled']
    compound=next(g for g in c['groups'] if g['fusion']=='conjunction-with-shared-argument')
    assert len(compound['satellites'][0]['fused_paths'])==2
    assert sum(g['shared_argument'] is not None for g in c['groups'])==3
    assert len(c['groups'])==5
    # Sharing requires the SAME argument, not merely calls of the same arity.
    value=deepcopy(c['source'])
    def change_one(node):
        if isinstance(node,dict):
            if node.get('kind')=='call' and node.get('symbol')=='round':
                node['arguments'][0]={'kind':'call','symbol':'town','arguments':[]}
            for v in node.values():change_one(v)
        elif isinstance(node,list):
            for v in node:change_one(v)
    change_one(value)
    assert not any(e.get('fusion')=='conjunction-with-shared-argument' for e in events(display_tree(value)))
    quoted={'kind':'quote','body':deepcopy(c['source']['body'])}
    assert not any(e.get('fusion') for e in events(display_tree(quoted)))


def test_outer_rail_crossings_are_uncommon_and_never_consecutive_in_the_main_flow():
    jumps=links=0
    for e in specimens()['entries']:
        groups=e['compiled']['groups']
        crossings=[abs(a['y']-b['y'])==64 for a,b in zip(groups,groups[1:])]
        assert not any(a and b for a,b in zip(crossings,crossings[1:]))
        jumps+=sum(crossings);links+=len(crossings)
        for g in groups:
            for s in g['satellites']:
                jumps+=abs(s['y']-g['y'])==64;links+=1
    assert jumps/links<.12


def test_actual_svg_contacts_are_radial_and_no_rendered_line_crosses_a_center():
    root=ET.fromstring((OUT/'overview.svg').read_text(encoding='utf-8'))
    ns='{http://www.w3.org/2000/svg}'
    circles=[(float(c.attrib['cx']),float(c.attrib['cy']),float(c.attrib['r'])) for c in root.iter(ns+'circle')]
    strokes=[]
    for p in root.iter(ns+'path'):
        if p.attrib['stroke']!='#203438':continue
        _,ax,ay,_,bx,by=p.attrib['d'].split()
        strokes.append(tuple(map(float,(ax,ay,bx,by))))
    contacts=0
    for ax,ay,bx,by in strokes:
        dx,dy=bx-ax,by-ay; length=math.hypot(dx,dy)
        for cx,cy,r in circles:
            t=((cx-ax)*dx+(cy-ay)*dy)/length**2
            nearest=math.hypot(cx-ax-max(0,min(1,t))*dx,cy-ay-max(0,min(1,t))*dy)
            if nearest>r+1e-6:continue
            contacts+=1
            assert abs((cx-ax)*dy-(cy-ay)*dx)/length<1e-6
            assert not 1e-6<t<1-1e-6
    assert contacts>100
    spacing_check([circle(cx/SCALE,cy/SCALE,r/SCALE) for cx,cy,r in circles]
                  +[line((ax/SCALE,ay/SCALE),(bx/SCALE,by/SCALE)) for ax,ay,bx,by in strokes])


def test_eight_rays_remain_available_without_forcing_them_into_the_specimens():
    for radius,pair in ((MEDIUM,None),(LARGE,None),(LARGE,'nested')):
        for direction in range(8):
            n=nucleus(0,32,radius,pair,direction)
            assert geometry_check(n['shapes'],n['paths'])
    groups=[g for e in specimens()['entries'] for g in e['compiled']['groups']]
    modes=Counter(g['stroke_mode'] for g in groups)
    assert .2<modes['radius']/len(groups)<.45
    assert sum(modes[m] for m in ('none','incoming','entry'))>modes['radius']
    assert sum(g['pair'] in ('offset','offset-left') for g in groups)/len(groups)<.2
    c=specimens()['entries'][7]['compiled']
    assert visible(c)==visible(compile_expression(c['source'],reference_order=c['reference_order']))


def test_compound_placement_candidates_and_non_repeated_right_angle_are_available():
    for radius,companion in ((MEDIUM,SMALL),(LARGE,SMALL),(LARGE,MEDIUM)):
        for pair in ('offset','offset-left'):
            legal=[]
            for direction in range(8):
                n=nucleus(0,32,radius,pair,direction,companion)
                try: geometry_check(n['shapes'],n['paths'])
                except ValueError:continue
                legal.append(direction)
            assert legal,(radius,companion,pair)
    # The permitted two tangencies remain available, with only one partner.
    assert geometry_check([circle(0,0,MEDIUM),circle(0,32,SMALL),line((0,0),(0,MEDIUM))],[])
    end=MEDIUM/math.sqrt(2)
    assert geometry_check([circle(0,0,MEDIUM),circle(32,32,MEDIUM),line((0,0),(end,end))],[])
    corners=sum(abs((b[0]-a[0])*(c[0]-b[0])+(b[1]-a[1])*(c[1]-b[1]))<EPS
                for e in specimens()['entries'] for path in e['compiled']['paths'] for a,b,c in zip(path,path[1:],path[2:]))
    assert corners>0


def test_minimum_separation_rejects_near_misses_crowded_ports_and_crossings():
    ring=circle(0,32,MEDIUM)
    y=32+MEDIUM+MIN_GAP-1
    with pytest.raises(ValueError,match='too close to another circle'):
        spacing_check([ring,line((-40,y),(40,y))])
    spacing_check([ring,line((-40,y+1),(40,y+1))])
    with pytest.raises(ValueError,match='line segments are too close'):
        spacing_check([line((0,0),(40,0)),line((0,MIN_GAP-1),(40,MIN_GAP-1))])
    with pytest.raises(ValueError,match='Unintended crossing'):
        spacing_check([line((0,0),(40,40)),line((0,40),(40,0))])
    # Two 45-degree-separated ports on the small ring would be too crowded.
    a=line((SMALL,32),(SMALL+32,32))
    b=line((SMALL/math.sqrt(2),32+SMALL/math.sqrt(2)),(32,64))
    with pytest.raises(ValueError,match='line segments are too close'):
        spacing_check([circle(0,32,SMALL),a,b])
    spacing_check([circle(0,32,SMALL),a,line((0,32+SMALL),(0,64))])


def test_center_and_rim_only_large_diagonals_are_all_four_directions_and_free():
    forms=diagonal_witnesses()
    assert {(f['mode'],f['direction']) for f in forms}=={(mode,d) for mode in ('radius','outer') for d in (1,3,5,7)}
    for f in forms:
        assert geometry_check(f['shapes'],f['paths'])
        path=f['paths'][0];a,b=path
        assert abs(b[1]-32)==pytest.approx(LARGE)
        assert math.dist(a,(0,32))==pytest.approx(0 if f['mode']=='radius' else LARGE)
        with pytest.raises(ValueError,match='freely|too close'):
            geometry_check(f['shapes']+[line(b,(b[0],b[1]+5))],[])
    record=json.loads((OUT/'specimens.json').read_text(encoding='utf-8'))
    assert len(record['diagonal_witnesses'])==8
    assert all('display' in f for f in record['diagonal_witnesses'])


def test_incoming_strokes_actually_reach_the_center_and_reference_orders_remain_distinct():
    for e in specimens()['entries']:
        c=e['compiled']
        for g in c['groups']:
            if g['stroke_mode']=='incoming':
                edge=next(edge for edge in c['edges'] if edge['target']==g['path'])
                assert edge['kind']=='visible'
                assert edge['points'][-1]==pytest.approx((g['x'],g['y']))
            elif g['stroke_mode']=='entry':
                assert any(s['kind']=='line' and near(s['x2'],g['x']) and near(s['y2'],g['y'])
                           and s['x1']<g['x']-g['radius'] for s in c['shapes'])
    source=specimens()['entries'][2]['compiled']
    geometries=[]
    for args in permutations(source['source']['body']['arguments']):
        changed=deepcopy(source['source']);changed['body']['arguments']=list(args)
        geometries.append(visible(compile_expression(changed,reference_order=source['reference_order'])))
    assert len(set(geometries))==6


def test_center_free_medium_and_small_circles_can_receive_all_eight_radial_ports():
    for radius in (SMALL,MEDIUM):
        for direction in range(8):
            dx,dy=math.cos(direction*math.pi/4),math.sin(direction*math.pi/4)
            a=(radius*dx,32+radius*dy);b=((radius+MIN_RUN)*dx,32+(radius+MIN_RUN)*dy)
            assert geometry_check([circle(0,32,radius),line(a,b)],[ [a,b] ])


def test_external_connections_can_terminate_at_a_medium_center_from_eight_directions():
    for direction in range(8):
        dx,dy=math.cos(direction*math.pi/4),math.sin(direction*math.pi/4)
        distance=32*math.sqrt(2) if direction%2 else 32 if direction in (2,6) else 80
        a=dict(x=-dx*distance,y=32-dy*distance,radius=SMALL)
        b=dict(x=0,y=32,radius=MEDIUM)
        circles=[circle(a['x'],a['y'],SMALL),circle(0,32,MEDIUM)]
        connection=route(a,b,circles,end_center=True)
        assert connection is not None
        path,lines=connection
        assert path[-1]==(0,32)
        assert geometry_check(circles+lines,[path])


def test_columns_are_local_preserve_every_reference_and_actually_reduce_width():
    comparisons=layout_comparison()
    assert 1<=sum(r['columns'] for r in comparisons)<=4
    assert all(r['saved']>=-EPS for r in comparisons)
    total_before=sum(r['without_columns'] for r in comparisons)
    assert 0<sum(r['saved'] for r in comparisons)/total_before<.05
    for entry in specimens()['entries']:
        c=entry['compiled']
        for i,g in enumerate(c['groups']):
            if not g['stacked']: continue
            previous=c['groups'][i-1]
            assert g['path'][:-1]==previous['path'][:-1]
            assert not previous['stacked'] and not g['satellites'] and not previous['satellites']
            assert near(g['x'],previous['x']) and not near(g['y'],previous['y'])
            changed=deepcopy(c['tree'])
            def at(path):
                n=changed
                for slot in path:n=n['children'][slot]['node']
                return n
            a,b=at(previous['path']),at(g['path'])
            if a['payload']!=b['payload']:
                a['payload'],b['payload']=b['payload'],a['payload']
                raw=restore(expanded_tree(changed))
                assert visible(c)!=visible(compile_expression(raw,reference_order=c['reference_order']))


def test_kant_supplement_is_a_referenced_definition_not_additional_source_text():
    first,second,supplement=specimens()['entries'][6:9]
    assert first['display_role']==second['display_role']=='main-assertion'
    assert supplement['display_role']=='expanded-reference'
    assert supplement['referenced_by']==second['expanded_definition']=='r2lo'
    def referenced(node):
        if isinstance(node,dict):
            if node.get('symbol')=='r2ll':return True
            return any(referenced(v) for v in node.values())
        return isinstance(node,list) and any(referenced(v) for v in node)
    assert referenced(second['compiled']['source'])
    assert supplement['definition']=='r2ll'
