from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.circle_contact_script import *
from scripts.proof_circle_contact_script import result, SOURCE, PROFILE
from scripts.proof_circle_contact_papers import paper_data, math_contour


def visible(sentence):
    return json.dumps(sentence['shapes'],sort_keys=True)


def test_exact_dimension_solution_and_only_allowed_contacts():
    assert math.isclose(MEDIUM+SMALL,PITCH)
    assert math.isclose(LARGE-MEDIUM,MEDIUM-SMALL)
    assert math.isclose(2*MEDIUM,math.hypot(PITCH,PITCH))
    for a,b in [(circle(0,0,SMALL),circle(0,PITCH,MEDIUM)),
                (circle(0,0,MEDIUM),circle(PITCH,PITCH,MEDIUM)),
                (circle(0,PITCH,LARGE),circle(LARGE,PITCH,SMALL)),
                (circle(0,PITCH,MEDIUM),circle(0,PITCH,SMALL))]:
        assert legal_pair(a,b)
    assert not legal_pair(circle(0,32,LARGE),circle(0,64,MEDIUM))
    assert not legal_pair(circle(0,32,SMALL),circle(2*SMALL,32,SMALL))
    assert not legal_pair(circle(0,32,MEDIUM),circle(10,32,SMALL))


def assert_connected(sentence):
    image=Image.new('L',(math.ceil(sentence['width']*4),112*4))
    draw=ImageDraw.Draw(image)
    for s in sentence['shapes']:
        if s['kind']=='circle':
            x,y,r=s['x']*4,(s['y']+24)*4,s['r']*4
            r+=3  # Center the 6-pixel outline on the mathematical circle.
            draw.ellipse(tuple(round(v) for v in (x-r,y-r,x+r,y+r)),outline=1,width=6)
        else:
            draw.line([(round(s['x1']*4),round((s['y1']+24)*4)),
                       (round(s['x2']*4),round((s['y2']+24)*4))],fill=1,width=6)
    point=next((x,y) for y in range(image.height) for x in range(image.width) if image.getpixel((x,y)))
    ImageDraw.floodfill(image,point,2)
    assert image.histogram()[1]==0


def test_samples_obey_new_geometry_are_connected_without_a_shared_line_spine():
    for sentence in result()['sentences']:
        assert geometry_check(sentence['shapes'])
        topology=line_topology([s for s in sentence['shapes'] if s['kind']=='line'])
        assert topology['components']>1
        assert topology['cycles']==topology['arrows']==0
        assert_connected(sentence)


@pytest.mark.parametrize('shapes',[
    [circle(0,0,LARGE)],
    [dict(kind='dot',x=0,y=32,r=2)],
    [circle(0,32,MEDIUM),line((-40,40),(40,40))],
    [circle(0,32,MEDIUM),line((0,32),(5,32))],
    [line((0,32),(32,0)),line((32,0),(64,32)),line((64,32),(32,64)),line((32,64),(0,32))],
    [line((50,32),(30,12)),line((50,32),(30,52)),line((50,32),(0,32))],
])
def test_forbidden_large_circle_dot_nonradial_endpoint_loop_arrow_are_rejected(shapes):
    with pytest.raises(ValueError):geometry_check(shapes)


def test_adding_a_relation_changes_the_existing_action_nucleus():
    trust,compound=result()['sentences'][1:3]
    get=lambda s:next(n for n in s['nodes'] if n.get('feature')=='action')
    assert get(trust)['radius']==MEDIUM
    assert get(compound)['radius']==LARGE
    assert any(e['placement']=='contact' for e in compound['links'])
    assert any(n.get('absorbed')==['participant'] for n in compound['nodes'])
    assert visible(trust)!=visible(compound)


def test_identifier_spelling_is_not_the_visual_code():
    text=Path(SOURCE).read_text(encoding='utf-8')
    profile=json.loads(Path(PROFILE).read_text(encoding='utf-8'))
    for old,new in [('ax','expectation'),('ay','reliance'),('ae','benefit'),('ac','firstperson'),('ad','secondperson')]:
        text=text.replace(old,new)
        for section in ('references','relations'):
            if old in profile[section]:profile[section][new]=profile[section].pop(old)
    assert [visible(s) for s in compile_document(text,profile)['sentences']]==[visible(s) for s in result()['sentences']]


def test_logical_connections_and_negation_scope_are_distinct():
    data=result()['sentences']
    assert len({visible(data[i]) for i in (3,5,6,7)})==4
    assert data[3]['scopes'][0]['exit_port']=='center'
    assert data[6]['scopes'][0]['exit_port']=='rim'
    profile=json.loads(Path(PROFILE).read_text(encoding='utf-8'))
    profile['relations']['ax']['features'].append('positive')
    with pytest.raises(ValueError,match='Repeated positive'):
        compile_document(Path(SOURCE).read_text(encoding='utf-8'),profile)


def evaluate_plan(plan,table,names):
    if plan['kind']=='bundle':
        pair=tuple(p['identity'] for p in plan['participants'])
        return all(table[(names[tuple(r['features'])],*pair)] for r in plan['relations'])
    values=[evaluate_plan(c,table,names) for c in plan['children']]
    return {'and':lambda:all(values),'or':lambda:any(values),'not':lambda:not values[0],
            'implies':lambda:not values[0] or values[1]}[plan['kind']]()


def test_eight_sentence_plans_match_native_truth_in_64_interpretations():
    data=result()
    slots=[(r,*pair) for r in ('ax','ay','ae') for pair in (('aki','nao'),('nao','aki'))]
    names={tuple(spec['features']):name for name,spec in data['profile']['relations'].items()}
    for bits in product((False,True),repeat=6):
        table=dict(zip(slots,bits))
        primitives={name:(lambda a,b,name=name:table.get((name,a,b),False)) for name in ('ax','ay','ae')}
        primitives.update(ac=lambda:'aki',ad=lambda:'nao')
        original=evaluate_document(data['source'],individuals=('aki','nao'),situations=('scene',),primitives=primitives)
        assert [r['value'] for r in original]==[evaluate_plan(s['plan'],table,names) for s in data['sentences']]


def test_original_quotes_and_native_equation_binding_are_preserved():
    data=paper_data()
    kant=json.loads(Path(data['kant']['source']).read_text(encoding='utf-8'))
    assert data['kant']['text']==kant['source']['text']
    assert 'beinahe unausbleiblich' in data['kant']['text']
    assert data['equations'][0]['printed']=='t_B − t_A = t′_A − t_B'
    assert data['equations'][1]['printed']=='ξ=β(x−vt)'
    # Check the actual typed source definition: two differences have the same
    # reflection reading in opposite operand slots, not two unrelated names.
    header=('n: r ba[h[b] c] c. r bf[h[b] c h[b] c] h[b] c. '
            'r sca[h[b] c h[b] c] c. r eisjo[] h[b] c. r eisjp[] h[b] c. r eisjq[] h[b] c. ')
    document=parse(header+' '.join(data['native_math']))
    defs={d['name']:d for d in document['declarations']}
    body=defs['eimi']['body']
    while body['kind']=='and':body=body['arguments'][1]
    assert body['symbol']=='sca'
    a,b,c=[p['name'] for p in defs['eimi']['parameters']]
    assert [[arg['name'] for arg in diff['arguments']] for diff in body['arguments']]==[[b,a],[c,b]]
    assert [n['symbol'] for n in defs['eims']['body']['body']['arguments']]==['eisjo','eisjp','eisjq']
    expr=data['equations'][0]['expression']
    assert expr['arguments'][0]['arguments'][0]==expr['arguments'][1]['arguments'][1]
    assert 'not implemented' in data['kant']['rendering']


def test_math_uses_same_contact_constraints_and_preserves_operator_order():
    data=paper_data()
    for equation in data['equations']:
        shape=math_contour(equation['expression'],data['quantities'])
        assert geometry_check(shape['shapes'])
        assert_connected(shape)
    expr=deepcopy(data['equations'][0]['expression'])
    original=math_contour(expr,data['quantities'])
    expr['arguments'][0]['arguments'].reverse()
    assert visible(original)!=visible(math_contour(expr,data['quantities']))
