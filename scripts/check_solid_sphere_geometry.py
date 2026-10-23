"""Check solid-ball coverage, independently defined boundary and current records."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import model as body_model,DOMAIN,refused,relations
from scripts.compose_solid_sphere_geometry import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/solid-sphere-geometry-v1.md';SOURCE='data/einstein-solid-sphere-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-physical-meaning-heading-review-v1.json'
DEPENDENCIES=('reports/physical-meaning-heading-v1.json','reports/rigid-body-kinematics-v1.json','reports/material-body-motion-v1.json','reports/rod-geometry-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time'}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'eje3':{'eje2'},'eje5':{'eigy','eiah','eje4'},'eje6':{'eiyx','sb'},'eje7':{'eiad','eje6'},'ejfa':{'eiyx','eje3'},'ejfb':{'eixu','eje5','eje7'},'ejfc':{'ejfb','eje7','eipf','eioj'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))=={'eje3':4,'eje4':3,'eje5':1,'eje7':1}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jssg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=('context','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def geometry_checks():
    cuts,m=numbers();c=cuts.make;count=0
    for center in ((0,0,0),(2,-1,3)):
        for xyz,radius in product(product((-1,0,1),repeat=3),(-1,0,1,2)):
            pos=[Q(a+b) for a,b in zip(center,xyz)];args=[c(Q(n)) for n in (*pos,*center,radius)];square=sum(Q(x)**2 for x in xyz)
            for name,expected in (('ejey',radius>0 and square<radius**2),('ejez',radius>0 and square<=radius**2)):
                assert run(name,args,m)==expected;count+=1
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make
    members.clear();members.update(('p','q'));pos['p']=[Q(0),Q(1),Q(0)];pos['q']=[Q(1),Q(0),Q(1)]
    snap=[pop,*fs,c(Q(1))]
    for xyz,expected in (((0,1,0),True),((1,0,1),True),((0,0,0),False),((1,1,1),False)):
        assert run('eje2',snap+[c(Q(n)) for n in xyz],m,domain=('p','q'))==expected;count+=1
    members.remove('p');assert not run('eje2',snap+[c(Q(n)) for n in (0,1,0)],m,domain=('p','q'));count+=1;members.add('p')
    # All coordinates are explicit, even for nonmembers visited by eager logic.
    pos['p']=[Q(0)]*3;pos['q']=[Q(1),Q(0),Q(0)];args=snap+[c(Q(n)) for n in (0,0,0,1)]
    for xyz,expected in (((0,0,0),True),((1,0,0),True),((0,1,0),False),((Q(1,2),0,0),False),((2,0,0),True)):
        assert run('eje4',args+[c(Q(n)) for n in xyz],m,'instance',('p','q'))==expected;count+=1
    pos['q'][0]=Q(2);assert not run('eje4',args+[c(Q(0))]*3,m,'instance',('p','q'));count+=1
    members.remove('q');assert run('eje4',args+[c(Q(0))]*3,m,'instance',('p','q'));count+=1
    refused(lambda:run('eje4',args,m,domain=('p','q')))
    unknowns(lambda mm:run('eje4',args+[c(Q(0))]*3,mm,'instance',('p','q')),m,('ba','bc','sca'))
    # Analytic closed-ball occupancy is an explicit test boundary, not a
    # finite material population being certified as an entire solid ball.
    analytic=m|{'eje2':lambda *xs:sum(cuts.read(x)**2 for x in xs[-3:])<=1}
    for xyz,eps,out,expected in (((1,0,0),Q(1,2),(Q(5,4),0,0),True),((0,1,0),Q(1,2),(0,Q(5,4),0),True),((0,0,-1),Q(1,2),(0,0,Q(-5,4)),True),((0,0,0),Q(1,2),(Q(1,4),0,0),False),((0,0,0),Q(1,2),(2,0,0),False),((2,0,0),Q(1,2),(Q(9,4),0,0),False),((1,0,0),Q(1,2),(Q(3,2),0,0),False)):
        assert run('eje3',snap+[c(Q(n)) for n in (*xyz,eps,*out)],analytic,'instance',('p','q'))==expected;count+=1
    refused(lambda:run('eje3',snap+[c(Q(n)) for n in (1,0,0)],analytic,domain=('p','q')))
    unknowns(lambda mm:run('eje3',snap+[c(Q(n)) for n in (1,0,0,Q(1,2),Q(5,4),0,0)],mm,'instance',('p','q')),analytic,('eje2','bg','ba'))
    return dict(cases=count,open_and_closed_balls_distinguished=True,same_material_point_for_all_coordinates=True,containment_and_complete_coverage_distinguished=True,boundary_uses_independent_occupancy_and_open_neighborhood=True,boundary_analytic_occupancy_is_explicit_test_boundary=True,unbounded_coverage_and_neighborhood_refused=True)

@lru_cache(None)
def history_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;count=0
    sphere=[c(Q(n)) for n in (0,0,0,2)];args=fields+sphere;snapshot=[pop,*fs,c(Q(1)),*sphere]
    rows={'eigy':{norm(fields)},'eiah':{norm(fields)},'eje4':{norm(snapshot)}};m=relations(m,rows,norm)
    check=lambda mm:run('eje5',args+[c(Q(1))],mm,'instance');count+=perturb(check,m,rows,norm)
    for low,high in ((1,1),(2,1)):
        bad=args[:];bad[5:7]=[c(Q(low)),c(Q(high))]
        assert not run('eje5',bad+[c(Q(1))],m|{n:lambda *xs:True for n in rows},'instance');count+=1
    # An out-of-interval query is not an extra obligation.
    assert run('eje5',args+[c(Q(3))],m,'instance');count+=1
    refused(lambda:run('eje5',args,m))
    return dict(cases=count,same_full_history_rigidity_rest_and_snapshot_required=True,positive_interval_and_same_center_radius_required=True,native_all_real_times_refused=True)

@lru_cache(None)
def record_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model(True);c=cuts.make;count=0
    values={'x':Q(3),'y':Q(1),'z':Q(0),'time':Q(1)}
    rows={'eiyx':{('event','record','K','context')},'sb':{('q','event','K','context','length','duration',Q(1),Q(3),Q(1),Q(0))}}
    m=relations(m,rows,norm)|{'zc6':lambda rec,role:c(values[role]) if rec=='record' and role in values else forbidden()}
    args=['body','q','event','record','K','context'];check=lambda mm:run('eje6',args,mm);count+=perturb(check,m,rows,norm)
    members.remove('q');assert not check(m);count+=1;members.add('q')
    for role in ('x','y','z','time'):
        values[role]+=1;assert not check(m|{'sb':lambda *xs:True});count+=1;values[role]-=1
    for t in (-1,3):
        values.update(time=Q(t),x=Q(3*t));assert not check(m|{'sb':lambda *xs:True});count+=1
    values.update(time=Q(1),x=Q(3));unknowns(check,m,('zc6','eislu','eirh','eisls','eislt'))
    rows={'eiyx':{('event','record','K','context')},'eje3':{norm([pop,*fs,c(Q(1)),c(Q(3)),c(Q(1)),c(Q(0))])}}
    m=relations(m,rows,norm);check=lambda mm:run('ejfa',['body','event','record','K','context'],mm)
    count+=perturb(check,m,rows,norm)
    assert check(m|{'sb':forbidden,'eje6':forbidden});count+=1
    return dict(cases=count,current_event_worldline_and_same_material_coordinate_family_required=True,member_and_time_and_every_coordinate_checked=True,surface_event_need_not_be_material_worldline_event=True)

@lru_cache(None)
def coverage_checks():
    # Two individuals distinguish all point/event/record slots. Only the real
    # time quantifier is exposed; individual quantifiers execute natively.
    cuts,m=numbers();c=cuts.make;r=cuts.read;domain=('p','q');count=0
    fs=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:c(Q(i)))) for i in range(3)]
    pop={'p','q'};rows={('p','p','q','p','q','context'),('p','q','p','q','q','context')}
    m|={'eirh':lambda b,p,s:(b,s)==('p','context') and p in pop,'eislu':lambda *xs:fs[0],'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eiad':lambda *xs:True,'eje6':lambda *xs:xs in rows,'zc6':lambda rec,role:c(Q(1)),'ta':lambda:'p','rb':lambda:'q','yn':lambda:'p','yo':lambda:'q','yp':lambda:'p','zc7':lambda:'q'}
    check=lambda mm:run('eje7',['p','q','context',c(Q(1))],mm,'instance',domain)
    count+=perturb(check,m,{'eje6':rows})
    assert not check(m|{'eiad':lambda *xs:False});count+=1
    for rec in domain:
        assert not check(m|{'zc6':lambda x,a,rec=rec:c(Q(2 if x==rec else 1))});count+=1
    assert not check(m|{'eislt':lambda *xs:c(Q(0))});count+=1
    assert run('eje7',['p','q','context',c(Q(3))],m,'instance',domain);count+=1
    refused(lambda:run('eje7',['p','q','context'],m,domain=domain))
    unknowns(check,m,('eiad','eislu','eirh','zc6'))
    return dict(cases=count,every_member_event_record_slot_checked_on_two_individuals=True,native_individual_quantifiers_preserved=True,same_time_current_record_required=True,complete_history_boundary_required=True)

@lru_cache(None)
def setting_checks():
    cuts,m,pos,members,fs,pop,fields,norm=body_model();c=cuts.make;count=0
    rows={'zbv':{('k','low','context')},'eixu':{('low','k',a,Q(0),'context') for a in ('x','y','z')},'eje5':{norm(fields+[c(Q(n)) for n in (0,0,0,2)])},'eje7':{('body','k','context')}}
    m=relations(m,rows,norm)|{'zbn':lambda *xs:'low' if xs==('k','context') else forbidden()}
    count+=perturb(lambda mm:run('ejfb',['body','k','context',c(Q(2))],mm),m,rows,norm)
    unknowns(lambda mm:run('ejfb',['body','k','context',c(Q(2))],mm),m,('eirh','eislu','eisls','eislt','zbn'))
    # Keep the two frames' intervals distinct while binding the same body.
    moving=fields[:];moving[1]='K';moving[6]=c(Q(3));speed=c(Q(4))
    m|={'eisls':lambda f,u,s:c(Q(0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(3 if f=='K' else 2)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislu':lambda b,f,lu,tu,a,s:fs[('x','y','z').index(a)] if b=='body' and f in ('K','k') and (lu,tu,s)==('length','duration','context') and a in ('x','y','z') else forbidden(),'zb7':lambda:speed}
    rows={'ejfb':{('body','k','context',Q(2))},'eje7':{('body','K','context')},'eipf':{norm(moving+[speed])},'eioj':{('K','k','length','duration','context')}}
    velocity={'x':Q(4),'y':Q(0),'z':Q(0)}
    m=relations(m,rows,norm)|{'eislc':lambda a,b,lu,tu,axis,s:c(velocity[axis]) if (a,b,lu,tu,s)==('K','k','length','duration','context') and axis in velocity else forbidden()}
    check=lambda mm:run('ejfc',['body',c(Q(2)),'context'],mm);count+=perturb(check,m,rows,norm)
    for axis in velocity:
        velocity[axis]+=1;assert not check(m);count+=1;velocity[axis]-=1
    assert not check(m|{n:lambda *xs:True for n in rows}|{'ra':lambda:'k','eislc':lambda a,b,lu,tu,axis,s:c(velocity[axis])});count+=1
    unknowns(check,m,('eirh','eislu','eisls','eislt','eislc','zb7'))
    return dict(cases=count,actual_measured_origin_and_complete_rest_shape_required=True,same_body_and_speed_in_material_and_frame_translation=True,frame_times_not_identified=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));units=[inv['units'][i-1] for i in (110,111,281)]
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-solid-sphere-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=['903'],segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])]) for u in units],observations=['u0110は同じ半径R、kでの静止、kの原点にある中心、Kに対する速度vを指定する。u0111の式はξ²+η²+ζ²=R²で、Kのt=0断面の式はまだ後続である。','u0281は原刊903頁下部の著者脚注。静止して調べたとき球の形を持つ物体、という説明を本文の同じ球へ結ぶ必要がある。inventoryのpage_at_end=921はこの脚注の実際の掲載頁ではない。','今回の閉球占有モデルは内部充填を含む明示的な理想化の候補であり、Kugelgestaltだけから必ず従うとは判断しない。著者の考察行為、球面式の提示、脚注の説明及び全文判断は未接続。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==327
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[326])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eigy','eiah','eipf','eiyx','eixu','eirh','sb'}<=names
    assert not names&{'eipc','eipe','shd','sfb','zhu','zhv','zbq'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=327,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('geometry',geometry_checks),('history',history_checks),('records',record_checks),('coverage',coverage_checks),('setting',setting_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_solid_sphere_geometry.py','scripts/check_solid_sphere_geometry.py','tests/test_solid_sphere_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_transverse_segment.py','scripts/check_translated_light_trial.py','scripts/check_rod_methods.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py'}
    return dict(status='closed_material_ball_boundary_and_current_records_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['閉球連続体という解釈の採用又は外形一般への拡張の判断','全現在記録の境界と球面式の同値への接続','原文u0110–u0111及び著者脚注u0281の提示と全文判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
