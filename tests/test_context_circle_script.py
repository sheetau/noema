from copy import deepcopy
from itertools import combinations
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from noema.constructed import parse
from scripts.context_circle_script import (
    compile_expression, geometry_check, pack_lines, restore, expanded_tree,
    SMALL, MEDIUM, LARGE, circle, line, near, EPS,
)
from scripts.proof_context_circle_script import specimens, OUT, KANT, SCALE, GUIDE


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
    with pytest.raises(ValueError,match='More than one stroke'):
        geometry_check([circle(0,32,MEDIUM),line((0,32),(MEDIUM,32)),line((0,32),(0,32+MEDIUM))],[])
    assert geometry_check([circle(0,32,MEDIUM),line((-MEDIUM,32),(MEDIUM,32))],[])
    rings=[circle(0,32,MEDIUM),circle(0,32,SMALL)]
    assert geometry_check(rings+[line((-MEDIUM,32),(-SMALL,32))],[])
    with pytest.raises(ValueError,match='without another rim'):
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
    with pytest.raises(ValueError,match='terminate freely'):
        geometry_check([circle(0,32,LARGE),diagonal,line((LARGE,32+LARGE),(LARGE,80))],[])


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
