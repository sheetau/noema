"""Check dimensions, same-time separation and directed calibration forces."""
from functools import lru_cache
from fractions import Fraction as Q
import json,re,xml.etree.ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,DescriptionValue,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import perturb,unknowns,forbidden,relation
from scripts.check_material_relative_frame import arithmetic,RS,NUM
from scripts.compose_point_charge_calibration import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,INDEX,MEANINGS,build

DOC='docs/point-charge-calibration-v1.md';SOURCE='data/einstein-point-charge-calibration-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p909-0.jpg'
PRIORS=tuple(f'data/einstein-field-symmetry-conclusion-u{n:04d}-review-v1.json' for n in (167,168,169,170,171,172,282))
DEPENDENCIES=('reports/field-symmetry-conclusion-v1.json','reports/charge-calibration-v1.json','reports/rest-force-v1.json','reports/electric-action-v1.json')
AXES=('x','y','z','t');SITUATIONS=('context','other')
CONSTANTS={'ri':'context','rd':'author','eirf':'paper','zno':'scope','ra':'frame','zol':'first','zom':'second','zon':'trial','zoo':'event','zop':'distancekind','zoq':'forcekind','zor':'chargekind','zos':'cm','zot':'dyn','zou':'chargeunit','zov':'distancerecord','zow':'forcerecord','zox':'chargerecord','eisqf':'secondrecord','zoy':'assumption','eisqj':'explanation','zik':'secondunit','zpn':'vectorforcekind',**dict(zip(('yn','yo','yp','zc7'),AXES))}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'other')))

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    abstract(doc,NUM);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpcc'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    if not any(d['name']=='ri' for d in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,_ in slots])
    if d['result']=='content':expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m
    for (n,s),x in zip(slots,args):mm[n]=lambda x=x:x
    return evaluate_document(doc,individuals=DOMAIN,situations=SITUATIONS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup(first=(0,0,0,4),second=(1,0,0,4),force=(0,1,0,0)):
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read
    point=lambda xs:FunctionValue(('individual',),RS,lambda role:c(dict(zip(AXES,xs)).get(role,0)))
    p1,p2,f=map(point,(first,second,force))
    def one(x):
        if isinstance(x,DescriptionValue):return json.loads(x.syntax)['symbol']
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',):return tuple(r(x(a)) for a in AXES)
        raise ValueError('Unknown calibration function fingerprint')
    norm=lambda xs:tuple(one(x) for x in xs);rel=lambda rows:lambda *xs:norm(xs) in rows
    rows={'eisqb':{('cm',Q(1),Q(0),Q(0),Q(1,100),'context'),('dyn',Q(1),Q(1),Q(-2),Q(1,100000),'context'),('secondunit',Q(0),Q(0),Q(1),Q(1),'context')},'eisqc':{('first','context')},'va':{('frame',)},'zoh':{('trial','first','second','frame','event','context')},'x4':{('first','frame','context')},'eisqd':{norm((body,'frame','event','cm','secondunit',p,'context')) for body,p in [('first',p1),('second',p2)]},'eisqe':{norm(('forcerecord','trial','first','second','frame','event','dyn',f,'context'))},'eirl':{('forcerecord','second','frame','event','context')},'zpc':{norm(('forcerecord','second','vectorforcekind','frame','event','dyn',f,'context'))},'zof':{(unit,kind,Q(1),'context') for unit,kind in [('chargeunit','chargekind'),('cm','distancekind'),('dyn','forcekind'),('dyn','vectorforcekind')]},'zog':{norm((record,target,kind,'frame','event',unit,c(1),'context')) for record,target,kind,unit in [('chargerecord','first','chargekind','chargeunit'),('secondrecord','second','chargekind','chargeunit'),('distancerecord','trial','distancekind','cm'),('forcerecord','trial','forcekind','dyn')]}}
    m|={'aa':lambda a,b:a<b,'ab':lambda a,b:a+b,'eisqg':lambda:p1,'eisqh':lambda:p2,'eisqi':lambda:f}|{n:rel(rs) for n,rs in rows.items()}
    return dict(c=c,r=r,m=m,point=point,p1=p1,p2=p2,force=f,norm=norm,rel=rel,rows=rows)

@lru_cache(None)
def unit_checks():
    s=setup();m=s['m'];norm=s['norm'];rows={'eisqb':s['rows']['eisqb']}
    cases=perturb(lambda mm:run('ejwc',[],mm),m,rows,norm)
    for scale,want in ((Q(1),True),(Q(0),False),(Q(-1),False)):
        assert run('ejwb',['cm',Q(1),Q(0),Q(0),scale,'context'],m|{'eisqb':lambda *xs:True})==want;cases+=1
    bad=set(rows['eisqb']);bad.remove(('dyn',Q(1),Q(1),Q(-2),Q(1,100000),'context'));bad.add(('dyn',Q(1),Q(1),Q(-1),Q(1,100000),'context'))
    assert not run('ejwc',[],m|{'eisqb':s['rel'](bad)});cases+=1
    assert Q(1,1000)*Q(1,100)==Q(1,100000)
    return dict(cases=cases,cm_dyn_second_dimensions_and_scales=True,gram_centimetre_second_force_conversion_exact=True,positive_scale_required=True)

@lru_cache(None)
def geometry_checks():
    s=setup();m=s['m'];p=s['point'];c=s['c'];cases=0
    for second,distance,want in [((1,0,0,4),1,True),((0,1,0,4),1,True),((0,0,1,4),1,True),((Q(3,5),Q(4,5),0,4),1,True),((1,0,0,5),1,False),((1,1,0,4),1,False),((0,0,0,4),0,True),((0,0,0,4),1,False),((1,0,0,4),-1,False)]:
        assert run('ejwd',[s['p1'],p(second),c(distance)],m)==want;cases+=1
    for vector,magnitude,want in [((1,0,0,0),1,True),((-1,0,0,0),1,True),((0,-1,0,0),1,True),((0,0,1,99),1,True),((Q(3,5),Q(4,5),0,0),1,True),((1,1,0,0),1,False),((0,0,0,0),1,False),((0,0,0,0),0,True),((1,0,0,0),-1,False)]:
        assert run('ejwe',[p(vector),c(magnitude)],m)==want;cases+=1
    assert not run('ejwd',[s['p1'],s['p2'],c(1)],m|{'ba':lambda x:False});cases+=1
    assert not run('ejwe',[s['force'],c(1)],m|{'yo':lambda:'x'});cases+=1
    return dict(cases=cases,native_three_dimensional_same_time_distance=True,native_vector_magnitude_not_component_sum=True,no_force_direction_fixed=True)

@lru_cache(None)
def calibration_checks():
    s=setup();m=s['m'];cases=perturb(lambda mm:run('ejwh',[],mm),m,s['rows'],s['norm'])
    unknowns(lambda mm:run('ejwh',[],mm),m,tuple(s['rows']))
    for first,second,force,want in [((0,0,0,4),(1,0,0,4),(0,0,-1,0),True),((0,0,0,4),(0,1,0,4),(Q(3,5),Q(4,5),0,0),True),((0,0,0,4),(1,0,0,5),(1,0,0,0),False),((0,0,0,4),(2,0,0,4),(1,0,0,0),False),((0,0,0,4),(1,0,0,4),(1,1,0,0),False)]:
        model=setup(first,second,force);assert run('ejwh',[],model['m'])==want;cases+=1
    assert run('ejwh',[],m|{'zoi':forbidden,'zok':forbidden,'xm':forbidden});cases+=1
    # The second target need not be at rest or be asserted pointlike.
    assert s['rows']['x4']=={('first','frame','context')} and s['rows']['eisqc']=={('first','context')}
    assert not run('ejwh',[],m|{'zom':lambda:'first'});cases+=1
    return dict(cases=cases,all_physical_record_argument_slots_checked=True,same_two_amount_records_and_directed_force=True,first_at_rest_second_not_required=True,old_undefined_point_or_equal_amount_predicates_not_used=True)

@lru_cache(None)
def presentation_checks():
    rows={'ug':{('assumption','author','ejwf','scope','context'),('explanation','author','ejwh','scope','context')},'uf':{('author','assumption','explanation','context')},'ue':{('assumption','explanation','context')}}
    m={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda mm:run('ejwi',[],mm),m,rows)
    assert run('ejwi',[],m|{'ejwf':forbidden,'ejwh':forbidden});cases+=1
    assert not run('ejwi',[],{n:lambda *xs:True for n in rows}|{'eisqj':lambda:'assumption'});cases+=1
    outer={'eir3':{('assumption','author','paper','ejwj','context')}}
    cases+=perturb(lambda mm:run('ejwk',[],mm),{n:relation(rs) for n,rs in outer.items()},outer)
    return dict(cases=cases,hypothetical_calibration_explanation_not_executed=True,author_and_order_preserved=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][172];assert u['id']=='einstein-1905:u0173' and digest(u['text'].encode())==u['text_sha256']
    start=u['text'].index('Es liegt');end=u['text'].index(' Nach dem');text=u['text'][start:end]
    m=next(m for m in inv['math'] if m['id']=='M0315');assert digest(m['mathml'].encode())==m['sha256'] and ''.join(ET.fromstring(m['mathml']).itertext())=='K'
    return dict(status='partial_physical_calibration_reading',unit=u['id'],unit_sha256=u['text_sha256'],range=[start,end],text=text,math=[m],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),observations=['原刊909頁のu0173第二文を再読した。punktförmig、Kで値1という仮定、d. h.の作用による説明、同じ量の別対象、第一対象の静止、1 cmと1 Dynを保持する。','校正で相手に及ぼす力と、後続で第一対象自身に働く力を区別する。第二対象の静止を加えず、力の方向は固定しない。'],remaining=['第一文の六式の解釈導入','第三文の現行相対性原理による移動系の値1','第四・第五文の現行の物理的な場と静止・瞬間静止への接続','第六文の二つの言い表しへの導入','u0173全体の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC,FACSIMILE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==358
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[INDEX]
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p in PRIORS:
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[157,158,159,160,161])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'sbw2','sbz2','x4','eirl','zpc','zoh'}<=names
    assert not names&{'zoi','zok','xm','sca2','sby2'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(json.dumps(source_record(),ensure_ascii=False))==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=4,new_references=5,replaced_statement=INDEX,other_357_statements_and_prior_judgments_preserved=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('units',unit_checks),('geometry',geometry_checks),('calibration',calibration_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_vacuum_field_domain','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_field_equations','compose_rest_force','compose_limits','check_moving_light_trip','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_point_charge_calibration.py','scripts/check_point_charge_calibration.py','tests/test_point_charge_calibration.py',*(f'scripts/{n}.py' for n in helpers)}
    s=source_record();row=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation')
    segments=[row]+[dict(row,math_id=m['id'],math_sha256=m['sha256']) for m in s['math']]
    return dict(status='physical_point_charge_calibration_dependency_connected',document=FULL,**results,alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=s['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
