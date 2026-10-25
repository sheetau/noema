from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image
import pytest

from noema.constructed import parse
from noema.constructed_semantics import evaluate_document
from scripts.branch_circle_script import *
from scripts.proof_branch_circle_script import specimens, OUT, KANT, SCALE, GUIDE


def visible(compiled):
    return json.dumps([word['shapes'] for word in compiled['words']],sort_keys=True)


def test_entire_syntax_round_trips_including_quotes_binders_and_empty_lists():
    for entry in specimens()['entries']:
        compiled=entry['compiled']
        assert restore(expanded_tree(compiled['tree']))==compiled['source']
    kant=specimens()['entries'][7]['compiled']
    tags={row[0] for row in kant['dictionary']}
    assert {'quote','function_ref'}<=tags
    quantified=specimens()['entries'][8]['compiled']
    assert {'content','forall','exists','variable'}<={row[0] for row in quantified['dictionary']}


def test_kant_is_actual_registered_syntax_and_not_a_sentence_placeholder():
    document=parse(Path(KANT).read_text(encoding='utf-8'))
    declarations={d['name']:d for d in document['declarations']}
    for entry in specimens()['entries'][6:8]:
        assert entry['original_assertion'] in document['statements']
        assert entry['compiled']['source']['body']==declarations[entry['expanded_definition']]['body']
        assert len(entry['compiled']['words'])>=5
    assert len(specimens()['entries'][7]['compiled']['words'])>=25


def test_every_word_obeys_revised_geometry_and_is_center_weighted():
    for entry in specimens()['entries']:
        for word in entry['compiled']['words']:
            assert geometry_check(word['shapes'],word['paths'])
            circles=[s for s in word['shapes'] if s['kind']=='circle']
            area=sum(c['r']**2 for c in circles)
            central=sum(c['r']**2 for c in circles if near(c['y'],32))
            assert central/area>=.5
            assert all(not near(c['r'],LARGE) or near(c['y'],32) for c in circles)


def test_branching_is_outside_the_circles_and_tangency_is_rare():
    branches=contacts=circles_count=0
    for entry in specimens()['entries']:
        for word in entry['compiled']['words']:
            circles=[s for s in word['shapes'] if s['kind']=='circle'];circles_count+=len(circles)
            adjacency={}
            for s in word['shapes']:
                if s['kind']=='line':
                    a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
                    adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
            for p,neighbors in adjacency.items():
                if len(neighbors)>=3 and all(math.dist(p,(c['x'],c['y']))>c['r']+EPS for c in circles):branches+=1
            for i,a in enumerate(circles):
                for b in circles[i+1:]:
                    contacts+=near(math.dist((a['x'],a['y']),(b['x'],b['y'])),a['r']+b['r'])
    assert branches>=20
    assert 0<contacts/circles_count<.05


def test_large_diagonal_must_be_terminal_and_free():
    diagonal=[(0,32),(LARGE,32+LARGE)]
    assert geometry_check([circle(0,32,LARGE),line(*diagonal)],[diagonal])
    bent=[(0,32),(32,64),(70,64)]
    with pytest.raises(ValueError,match='large-circle diagonal'):
        geometry_check([circle(0,32,LARGE)]+[line(a,b) for a,b in zip(bent,bent[1:])],[bent])
    extension=[diagonal[-1],(LARGE,42+LARGE)]
    with pytest.raises(ValueError,match='not free'):
        geometry_check([circle(0,32,LARGE),line(*diagonal),line(*extension)],[diagonal,extension])


def test_overlap_degree_center_strokes_and_continuous_right_angles_are_enforced():
    with pytest.raises(ValueError,match='more than one'):
        geometry_check([circle(0,32,r) for r in (SMALL,MEDIUM,LARGE)],[])
    with pytest.raises(ValueError,match='center stroke'):
        geometry_check([circle(0,32,LARGE)],[])
    paths=[[(0,0),(20,0)],[(20,0),(20,32)],[(20,32),(52,32)]]
    with pytest.raises(ValueError,match='right-angle'):
        geometry_check([line(*p) for p in paths],paths)
    rings=[circle(0,0,MEDIUM),circle(32,32,MEDIUM)]
    with pytest.raises(ValueError,match='nonradial'):
        geometry_check(rings+[line((0,32),(32,0))],[[(0,32),(32,0)]])
    assert geometry_check(rings+[line((0,0),(32,32))],[[(0,0),(32,32)]])


def test_reversing_participants_and_operands_changes_visible_geometry():
    source=specimens()['entries'][2]['compiled']
    changed=deepcopy(source['source'])
    changed['body']['arguments'][0],changed['body']['arguments'][2]=changed['body']['arguments'][2],changed['body']['arguments'][0]
    assert visible(source)!=visible(compile_expression(changed,reference_order=source['reference_order']))
    math_source=specimens()['entries'][9]['compiled']
    changed=deepcopy(math_source['source'])
    changed['arguments'][0]['arguments'].reverse()
    assert visible(math_source)!=visible(compile_expression(changed,reference_order=math_source['reference_order']))


def test_renaming_identifiers_does_not_change_geometry():
    compiled=specimens()['entries'][2]['compiled']
    mapping={'aki':'someone','nao':'another','book':'object','give':'transfer'}
    def rename(value):
        if isinstance(value,dict):return {k:(mapping.get(v,v) if k=='symbol' else rename(v)) for k,v in value.items()}
        if isinstance(value,list):return [rename(v) for v in value]
        return value
    registry={mapping.get(k,k):v for k,v in compiled['reference_order'].items()}
    assert visible(compiled)==visible(compile_expression(rename(compiled['source']),reference_order=registry))
    with pytest.raises(ValueError,match='registry'):
        compile_expression(compiled['source'],reference_order={})


def test_normal_examples_preserve_transfer_joint_witness_scope_and_condition():
    doc=specimens()['ordinary_source']
    domain=('town','bird','tree','aki','book','nao','home','apple','pear')
    constants={'town':'town','birdone':'bird','treeone':'tree','aki':'aki','book':'book','nao':'nao','home':'home'}
    for rain,inside,flies,common in product((False,True),repeat=4):
        model={name:(lambda value=value:value) for name,value in constants.items()}
        model.update(rain=lambda place:rain and place=='town',above=lambda a,b:(a,b)==('bird','tree'),
                     give=lambda a,b,c:(a,b,c)==('aki','book','nao'),fruit=lambda x:x in ('apple','pear'),
                     red=lambda x:x=='apple',round=lambda x:x==('apple' if common else 'pear'),
                     bird=lambda x:x=='bird',fly=lambda x:flies and x=='bird',
                     inside=lambda a,b:inside and (a,b)==('aki','home'))
        values=evaluate_document(doc,individuals=domain,situations=('scene',),primitives=model)
        assert [v['value'] for v in values]==[rain,True,True,common,not flies,not rain or inside]


def test_one_sheet_contains_visible_kant_ink_and_faint_guides_at_small_scale():
    image=Image.open(OUT/'overview.png').convert('RGB')
    data=json.loads((OUT/'specimens.json').read_text(encoding='utf-8'))
    assert image.size==(data['sheet']['width'],data['sheet']['height'])
    assert data['sheet']['scale']==SCALE<.6
    assert data['sheet']['guide_color']==GUIDE
    assert {e['section'] for e in data['entries']}=={'normal','kant','einstein'}
    for entry in data['entries'][6:9]:
        box=entry['display'];x,y=box['x'],box['y']
        crop=image.crop((x,y-12,x+box['width'],y+(box['rows']-1)*66+44)).convert('L')
        assert sum(crop.histogram()[:110])>200, 'Kant glyph region is blank or unreadably faint'
    root=ET.fromstring((OUT/'overview.svg').read_text(encoding='utf-8'))
    record=json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
    assert record['entries'][7]['compiled']['source']==data['entries'][7]['compiled']['source']
