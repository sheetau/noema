"""Check shared velocity-composition subjects and the source opening presentation."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_clock_transfer_records import physical,POINTS
from scripts.check_point_motion_records import DOMAIN as OLD_DOMAIN
from scripts.compose_velocity_opening_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,build

DOC='docs/velocity-opening-claim-v1.md';SOURCE='data/einstein-velocity-opening-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-curve-earth-u0128-review-v1.json'
READING='data/einstein-point-motion-records-source-reading-v1.json'
DEPENDENCIES=('reports/point-motion-records-v1.json','reports/frame-motion-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zb6':'context','zkb':'clock','rd':'author','eirf':'paper','ri':'discourse','eisdx':'part','eisoq':'section','eisor':'heading','eisos':'longitudinalname','eisot':'transversename','zjy':'previous','zkg':'setting'}
DOMAIN=tuple(dict.fromkeys((*OLD_DOMAIN,*CONSTANTS.values(),'inquiry')))
BOUNDS={'ejm2':{'eioj'},'ejm3':{'ejms'},'ejm4':{'ejm2','ejmv','ejm3'},'ejm7':{'ejmw'},'ejna':{'ejmw'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jvoc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jvocpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jvocpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jvocpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def relations(m,rows,norm):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}

@lru_cache(None)
def relative_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0
    for vector in ((0,0,0),(3,-2,7),(-9,1,0)):
        def velocity(first,second,lu,tu,axis,ctx):
            if (first,second,lu,tu,ctx)!=('K','k','length','duration','context') or axis not in ('x','y','z'):forbidden()
            return c(Q(vector[('x','y','z').index(axis)]))
        rows={'eioj':{('K','k','length','duration','context')}};mm=relations(m,rows,norm)|{'eislc':velocity};a=['K','k','context',*[c(Q(x)) for x in vector]]
        count+=perturb(lambda mm:run('ejm2',a,mm),mm,rows,norm)
        for i in range(3):
            bad=a[:];bad[3+i]=c(Q(vector[i])+1);assert not run('ejm2',bad,mm);count+=1
        unknowns(lambda mm:run('ejm2',a,mm),mm,('eislc',))
    return dict(cases=count,same_two_frames_units_and_all_three_relative_components=True,no_implicit_positive_direction_or_nonzero_speed_in_heading_topic=True)

@lru_cache(None)
def event_binding_checks():
    count=0;domain=('a','b')
    for event,record,place in product(domain,repeat=3):
        rows={'ejms':{('a',event,record,place,'b','context')}};mm={n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:run('ejm3',['a',event,'b','context'],mm,domain=domain),mm,rows)
    return dict(cases=count,both_current_record_and_place_share_the_given_event=True)

@lru_cache(None)
def composition_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0
    vector=[c(Q(x)) for x in (3,-2,7,11,5,-1,13,4,8)];a=['clock','K','k','context',*vector]
    rows={'ejm2':{norm(['K','k','context',*vector[:3]])},'ejmv':{norm(['clock','k',*vector[3:6],'context']),norm(['clock','K',*vector[6:],'context'])},'ejm3':{('clock',ev,frame,'context') for ev in ('event','arrival') for frame in ('K','k')}}
    mm=relations(m,rows,norm);count+=perturb(lambda mm:run('ejm4',a,mm),mm,rows,norm)
    for frame in ('K','k'):
        extra=rows['ejm3']|{('clock','departure',frame,'context')};assert not run('ejm4',a,mm|{'ejm3':relation(extra)});count+=1
    extra=rows['ejm3']|{('clock','departure',frame,'context') for frame in ('K','k')};assert run('ejm4',a,mm|{'ejm3':relation(extra)});count+=1
    # No finite numerical addition rule is imposed: supplied full physical histories
    # are the boundary here, and the two frames may assign different coordinate times.
    for slot in range(4,13):
        bad=a[:];bad[slot]=c(cuts.read(bad[slot])+1);assert not run('ejm4',bad,mm);count+=1
    return dict(cases=count,same_point_and_three_velocity_roles_bound=True,bidirectional_full_event_scope_not_coordinate_time_equality=True,full_histories_are_explicit_test_boundaries=True)

@lru_cache(None)
def designation_checks():
    cuts,m,coords,fs,norm=physical();c=cuts.make;count=0;m|={'zkc':lambda:c(Q(7)),'zkd':lambda:c(Q(-3))}
    rows={'ejmw':{norm(['clock','k',c(Q(7)),c(Q(-3)),'context'])}};mm=relations(m,rows,norm)
    for name,correct,other in (('ejm7',7,-3),('ejna',-3,7)):
        a=['clock',c(Q(correct)),'context'];count+=perturb(lambda mm:run(name,a,mm),mm,rows,norm)
        assert not run(name,['reference',*a[1:]],mm|{'ejmw':lambda *xs:True});count+=1
        for wrong in (other,0,correct+1):assert not run(name,['clock',c(Q(wrong)),'context'],mm);count+=1
        unknowns(lambda mm:run(name,a,mm),mm,('zkc','zkd'))
    return dict(cases=count,two_notations_bind_same_point_and_distinct_constant_components=True,component_not_position_or_frame_speed=True)

@lru_cache(None)
def presentation_checks():
    count=0
    table=(('ejm5',['inquiry','context'],{'eisoo':{('inquiry','ejm4','context')},'eisop':{('inquiry','context')}}),('ejm6',[],{'eisdv':{('heading','section','part','paper',Q(2),Q(5),'discourse')},'eisdw':{('heading','section','ejm5','discourse')},'ue':{('previous','heading','discourse')}}),('ejnb',[],{'ug':{('setting','author','ejmy','section','discourse')},'eislo':{('longitudinalname','ejm7','paper','discourse'),('transversename','ejna','paper','discourse')}}),('ejnd',[],{'eir3':{('setting','author','paper','ejnc','discourse')},'ue':{('heading','setting','discourse')}}))
    for name,a,rows in table:
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,a,mm),mm,rows)
        assert run(name,a,mm|{n:forbidden for n in ('ejm4','ejm7','ejna','ejmy','ejmv','se')});count+=1
    rows={'eisdv':{('heading','section','part','paper',Q(2),Q(5),'discourse')},'eisdw':{('heading','section','ejm5','discourse')},'ue':{('previous','heading','discourse')}};mm={n:relation(rs) for n,rs in rows.items()}
    for name,val in (('eisor','section'),('eisoq','part'),('zjy','heading')):
        assert not run('ejm6',[],mm|{p:lambda *xs:True for p in rows}|{name:lambda val=val:val});count+=1
    assert not run('ejnd',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'eisor':lambda:'setting'});count+=1
    return dict(cases=count,composition_and_theorem_are_separate_topic_roles=True,section_five_depth_two_and_same_source_order=True,assumption_and_two_notation_rules_attributed_without_execution=True)

@lru_cache(None)
def source_record():
    old=json.loads(read(READING));validate_hashes(ROOT,old['source_sha256']);rec=deepcopy(old)
    rec.update(version='einstein-velocity-opening-source-reading-v1',observations=[old['observations'][0],'見出しのAdditionstheoremを、物理的な速度の合成規則と条件を前提から導く定理の主題として読む。第一部内の第五節で、第二部直前のu0150までを案内する。','bewegeの仮定提示、三式とwobeiの二成分の説明を一つの設定文へ接続した。原点を通る条件、同じ点と二系、全期間での同じ二定数を保つ。見出しと本文の意味判断は局所検査とは別に記録する。',old['observations'][2]],source_sha256=old['source_sha256']|{p:digest((ROOT/p).read_bytes()) for p in (READING,DOC)})
    return rec

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==352
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[347,348,349])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    annotations=load_annotations(ROOT,BASIS,ANNOTATIONS);assert {e['symbol'] for e in annotations.annotations['entries']} >= {'eisos','eisot'}
    doc=core();names=lambda root:{d['name'] for d in extract_document(doc,roots=[root],statement_indices=[]).document['declarations']}
    assert {'eioj','ejmv','ejmu','se','eiyw','ejms','ejm3'}<=names('ejm4')
    assert not {'syt','sys','syq','zgj','zka','syu','syw','zke'}&names('ejm4')
    assert {'ejmy','ejmx','ejmw','eivz','syr','eislo'}<=names('ejnb')
    assert 'ug' not in names('ejm6') and 'eisop' in names('ejm6')
    assert len([d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive'])==6
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=350,prior_judgments_preserved=True,heading_not_specific_formula_or_completed_proof=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('relative',relative_checks),('events',event_binding_checks),('composition',composition_checks),('designation',designation_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_point_motion_records','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_point_motion_records','check_clock_transfer_records','check_clock_site_time','check_coordinate_correspondence','check_moving_trip_geometry','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_velocity_opening_claim.py','scripts/check_velocity_opening_claim.py','tests/test_velocity_opening_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[350 if i==0 else 351],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='velocity_composition_heading_and_planar_motion_assumption_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0129–u0132の各全単位判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
