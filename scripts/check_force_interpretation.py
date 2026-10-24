"""Check the electric subset and introduction of two prospective wordings."""
from functools import lru_cache
from itertools import product
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_moving_trip_geometry import NUM
from scripts.check_field_comparison_claim import setup
from scripts.check_vacuum_field_domain import sample_points,PS,AXES,POINTS
from scripts.compose_force_interpretation import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDICES,WHOLE_INDICES,MEANINGS,build

DOC='docs/force-interpretation-v1.md';SOURCE='data/einstein-force-interpretation-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg'
DEPENDENCIES=('reports/point-charge-calibration-v1.json','reports/moving-unit-charge-v1.json','reports/resting-charge-force-v1.json','reports/field-symmetry-conclusion-v1.json','reports/field-transform-v1.json')
CONSTANTS={'ri':'context','rd':'author','eirf':'paper','zno':'scope','eisqa':'sixdisplay','eisqm':'intro','eisqn':'transition','zoy':'assumption','zpg':'inference','zph':'standing','zpi':'instant','zpq':'firstwording','zpr':'secondwording',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'other')));SITUATIONS=('context','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'s6k'}|{'ejw7':{'ejub'},'ejxa':{'ejwf','ejwm','ejww','ejwx'},'ejxc':{'ejw7','ejxa'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='sample':
        doc=sample_points(doc);doc['declarations'][:0]=[dict(kind='primitive',name=n,parameters=[],result=PS) for n in ('jvfdone','jvfdtwo')]
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    d=next(d for d in doc['declarations'] if d['name']==name);expr=dict(kind='call',symbol=name,arguments=[])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc

def run(name,m,mode='boundary'):
    doc=fixture(name,mode);mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def contents(names,bits):return {n:lambda b=b:Content(SITUATIONS,(b,not b)) for n,b in zip(names,bits)}

@lru_cache(None)
def electric_checks():
    s=setup(1);m=s['m']|contents(('ejub',),(True,));cases=0
    assert run('ejw7',m,'sample');cases+=1
    for axis,pos in product(AXES[:3],POINTS[:2]):
        changed=s['scaled'](s['e'],1,axis,pos)
        assert not run('ejw7',m|{'znr':lambda changed=changed:changed},'sample');cases+=1
    # The current magnetic transform is not one of these three equations.
    assert run('ejw7',m|{'zns':forbidden,'s6l':forbidden},'sample');cases+=1
    outside=s['scaled'](s['e'],1,AXES[0],POINTS[2])
    assert run('ejw7',m|{'znr':lambda:outside},'sample');cases+=1
    assert not run('ejw7',m|contents(('ejub',),(False,)),'sample');cases+=1
    empty=s['region'](set());assert not run('ejw7',m|{'znt':lambda:empty},'sample');cases+=1
    unknowns(lambda mm:run('ejw7',mm,'sample'),m,('ejub','s6k','znr','znt'))
    try:run('ejw7',m)
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All real points silently sampled')
    return dict(cases=cases,three_electric_components_at_all_sampled_points=True,magnetic_transform_not_added=True,full_function_domain_refused=True,physical_background_and_inverse_mixture_are_explicit_boundaries=True)

@lru_cache(None)
def premise_checks():
    cases=0
    for name,names in [('ejxa',('ejwf','ejwm','ejww','ejwx')),('ejxc',('ejw7','ejxa'))]:
        for bits in product((False,True),repeat=len(names)):
            assert run(name,contents(names,bits))==all(bits);cases+=1
        unknowns(lambda mm:run(name,mm),contents(names,[True]*len(names)),names)
    return dict(cases=cases,unit_amounts_and_conditional_force_contents_shared=True)

@lru_cache(None)
def wording_checks():
    rows={'eisqo':{(n,'ejw7','ejxa','scope','context') for n in ('firstwording','secondwording')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejxb',mm),m,rows)
    assert run('ejxb',m|{n:forbidden for n in ('ejw7','ejxa','sco2','scp2')});cases+=1
    assert not run('ejxb',{'eisqo':lambda *xs:True,'zpr':lambda:'firstwording'});cases+=1
    return dict(cases=cases,two_distinct_wordings_same_target_and_interpretation=True,prospective_reference_not_execution_of_following_units=True)

@lru_cache(None)
def presentation_checks():
    notes=('assumption','inference','standing','instant','transition')
    intro={'eisox':{('sixdisplay','ejvm','context')},'uf':{('author','sixdisplay','intro','context'),*(('author','intro',n,'context') for n in notes)},'ue':{('intro','assumption','context')}}
    cases=perturb(lambda mm:run('ejxd',mm),{n:relation(rs) for n,rs in intro.items()},intro)
    assert run('ejxd',{n:relation(rs) for n,rs in intro.items()}|{'ejvm':forbidden});cases+=1
    end={'zc':{('transition','author','ejxc','ejxb','scope','context')},'eislk':{('firstwording','transition',Q(1),'paper','context'),('secondwording','transition',Q(2),'paper','context')},'uf':{('author','transition',n,'context') for n in ('firstwording','secondwording')},'ue':{('transition','firstwording','context'),('firstwording','secondwording','context')}}
    cases+=perturb(lambda mm:run('ejxe',mm),{n:relation(rs) for n,rs in end.items()},end)
    assert run('ejxe',{n:relation(rs) for n,rs in end.items()}|{'ejxc':forbidden,'ejxb':forbidden});cases+=1
    for name,node,prior,msg in [('ejxg','intro','sixdisplay','ejxf'),('ejxi','transition','instant','ejxh')]:
        rows={'eir3':{(node,'author','paper',msg,'context')},'ue':{(prior,node,'context')}}
        cases+=perturb(lambda mm:run(name,mm),{n:relation(rs) for n,rs in rows.items()},rows)
    for name,symbol,alias,relations in [('ejxd','eisqm','assumption',intro),('ejxe','zpr','firstwording',end)]:
        assert not run(name,{n:lambda *xs:True for n in relations}|{symbol:lambda alias=alias:alias});cases+=1
    return dict(cases=cases,interpretation_of_same_six_equations=True,mithin_and_following_first_second_items=True,author_and_order_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][172];assert u['id']=='einstein-1905:u0173' and digest(u['text'].encode())==u['text_sha256']
    starts=[0]+[u['text'].index(s) for s in ('Es liegt','Nach dem','Ruht diese','Ruht die Elektrizitätsmenge','Die ersten')]
    ends=starts[1:]+[len(u['text'])]
    parts=[dict(range=[a,b],text=u['text'][a:b],statements=[i]) for a,b,i in zip(starts,ends,WHOLE_INDICES)]
    assert ''.join(p['text'] for p in parts)==u['text'] and len(parts)==6
    ms=[next(m for m in inv['math'] if m['id']==mid) for mid in u['math_ids']]
    for m,expected in zip(ms,('K','X,Y,Z','X′,Y′,Z′')):
        assert digest(m['mathml'].encode())==m['sha256'] and ''.join(ET.fromstring(m['mathml']).itertext())==expected
    return dict(status='complete_six_sentence_source_collation_not_automatic_equivalence',unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],math=ms,sentences=parts,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),observations=['原刊909頁のu0173六文を通読した。直前の六式の解釈導入、仮定と校正、原理による値1、二つの静止条件、二つの言い表しへの帰結を連続して読む。','第六文の最初の三式は二段組の電気側X′,Y′,Z′。二つの言い方は続く番号1、2のu0174とu0175を指す。','原資料は変更しない。点状電気量・同じ対象と出来事・単位・条件・定義参照・著者の提示を全六文に共有する。'],remaining=['全六文の意味判断は別記録で行う','u0174以降と二作品全体の目標は未完'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==360 and new.document['statements'][:358]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[163,164,165,166])==selection_binding(old,[163,164,165,166])
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,sorted(WHOLE_INDICES))['dependencies'])
    assert set(MEANINGS)|{'ejwk','ejwp','ejw4','ejw6','ejs3','eisqo','eislk'}<=names
    assert not names&{'sco2','scp2','zpa','zoi','zok','xm'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_references=2,added_statements=INDICES,original_358_statements_preserved=True,whole_source_order=WHOLE_INDICES,semantic_judgment_separate=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('electric',electric_checks),('premise',premise_checks),('wording',wording_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_moving_trip_geometry','check_field_comparison_claim','check_vacuum_field_domain','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_force_interpretation.py','scripts/check_force_interpretation.py','tests/test_force_interpretation.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=part['range'],source=part['text'],statements=part['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for part in (s['sentences'][0],s['sentences'][-1])]
    return dict(status='force_interpretation_introductions_and_six_sentence_connection_checked',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
