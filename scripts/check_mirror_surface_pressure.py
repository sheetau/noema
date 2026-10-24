"""Check material coverage, same-event maps, physical patches and pressure queries."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_material_relative_frame import NUM,RS,FS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_translated_light_trial import expose
from scripts.compose_mirror_surface_pressure import *

DOC='docs/mirror-surface-pressure-v1.md';SOURCE='data/einstein-mirror-surface-pressure-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p914-0.jpg'
DEPENDENCIES=('reports/stationary-mirror-boundary-v1.json','reports/solid-sphere-geometry-v1.json','reports/material-body-motion-v1.json','reports/rigid-body-kinematics-v1.json','reports/wave-transform-application-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time'}
DOMAIN=('p','q','body','patch','K','k','length','duration','forceunit','process','scope','other','x','y','z','time')
PS=dict(kind='function',parameters=['individual'],result=RS)
BOUNDS_MAP={'ekqq':{'eigy','eiah','ekqp'},'ekqr':{'ekqq','eje7'},'ekqt':{'ekqs'},'ekqu':{'ekqr','eje7','eipf','eje6','ekqt'},'ekqz':{'ekqr','eiad'},'ekq3':{'sede'},'ekq4':{'ekqu','ekqz'},'ekq5':{'ekq4','sede'},'ekq6':{'ekq5'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'bg','be','sjd','sky','soy','szi','shu'}|BOUNDS_MAP.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall'},only_sort=RS))=={'ekqp':3,'ekqq':1,'ekqz':1}[name]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmsp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jmspcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jmspcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jmspcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def environment(individual_probes=('p','q','x','y','z')):
    cuts,m=arithmetic();c,r=cuts.make,cuts.read
    positions={'body':{'p':(0,0,0),'q':(0,3,4)},'patch':{'p':(0,0,0),'q':(0,3,4)}};members={'body':{'p','q'},'patch':{'p'}}
    def family(body,axis):
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:c(positions.get(body,{}).get(p,(0,0,0))[('x','y','z').index(axis)])))
    m|={'eirh':lambda b,p,ctx:ctx=='case' and p in members.get(b,set()),'eislu':lambda b,f,l,t,a,ctx:family(b,a),'eisls':lambda *xs:c(0),'eislt':lambda *xs:c(2)}
    def norm(x):
        if not isinstance(x,FunctionValue):return x
        if x.parameters==tuple(RS['parameters']) and x.result==RS['result']:return r(x)
        probes=[individual_probes if t=='individual' else ('case','other') if t=='situation' else tuple(map(c,(0,1,2))) for t in x.parameters]
        return tuple(norm(x(*ys)) for ys in product(*probes))
    normalize=lambda row:tuple(norm(x) for x in row)
    def hist(body,frame):return [body,frame,'case','length','duration',c(0),c(2),FunctionValue(('individual',),'truth',lambda p:p in members.get(body,set())),*(family(body,a) for a in ('x','y','z'))]
    return cuts,m,positions,members,family,hist,normalize

@lru_cache(None)
def plane_checks():
    cuts,m,pos,members,family,hist,norm=environment();c=cuts.make;cases=0
    snap=hist('body','k')[7:]+[c(1)]
    for xyz,expected in (((0,0,0),True),((0,3,4),True),((0,1,2),False),((1,0,0),True)):
        assert run('ekqo',snap+list(map(c,xyz)),m)==expected;cases+=1
        assert run('ekqp',snap+list(map(c,xyz)),m,'instance')==expected;cases+=1
    pos['body']['q']=(1,3,4)
    assert not run('ekqp',snap+list(map(c,(0,0,0))),m,'instance');cases+=1
    assert not run('ekqo',snap+list(map(c,(1,3,4))),m);cases+=1
    pos['body']['q']=(0,3,4);refused(lambda:run('ekqp',snap,m));cases+=1
    fields=hist('body','k');rows={'eigy':norm(fields),'eiah':norm(fields),'ekqp':norm(snap)}
    mm=m|{n:lambda *xs,row=row:norm(xs)==row for n,row in rows.items()}
    assert run('ekqq',fields+[c(1)],mm,'instance');cases+=1
    for n in rows:assert not run('ekqq',fields+[c(1)],mm|{n:lambda *xs:False},'instance');cases+=1
    assert run('ekqq',fields+[c(3)],mm,'instance');cases+=1
    bad=fields[:];bad[5]=c(2);assert not run('ekqq',bad+[c(1)],mm,'instance');cases+=1
    refused(lambda:run('ekqq',fields,mm));cases+=1
    expected=norm(fields);mm=m|{'ekqq':lambda *xs:norm(xs)==expected,'eje7':lambda *xs:xs==('body','k','case')}
    assert run('ekqr',['body','k','case'],mm);cases+=1
    for i,x in enumerate(('patch','K','other')):
        bad=['body','k','case'];bad[i]=x;assert not run('ekqr',bad,mm);cases+=1
    unknowns(lambda model:run('ekqr',['body','k','case'],model),mm,('ekqq','eje7','eislu','eisls','eislt'))
    return dict(cases=cases,containment_and_complete_plane_coverage_distinguished=True,same_material_history_rest_rigidity_and_current_records=True,finite_samples_not_an_entire_plane=True,unbounded_positions_and_times_refused=True)

@lru_cache(None)
def mapping_checks():
    cuts,m,pos,members,family,hist,norm=environment(('p','q'));c,r=cuts.make,cuts.read;cases=0
    selected=('body','p','q','p','q','case');m|={'ekqs':lambda *xs:xs==selected}
    for speed in (0,3,-3):
        beta=Q(1) if speed==0 else Q(5,4)
        for y,z,t in ((0,0,0),(2,-3,1),(-4,5,Q(-2,3))):
            records={'p':dict(zip(('x','y','z','time'),(beta*speed*t,y,z,beta*t))),'q':dict(zip(('x','y','z','time'),(0,y,z,t)))}
            mm=m|{'zc6':lambda rec,axis:c(records[rec][axis])}
            values=[*selected,c(5),c(speed)];assert run('ekqt',values,mm);cases+=1
            for rec in ('p','q'):
                for axis in ('x','y','z','time'):
                    records[rec][axis]+=1;assert not run('ekqt',values,mm),(speed,rec,axis);cases+=1;records[rec][axis]-=1
            for i,x in enumerate(('patch','q','p','q','p','other')):
                bad=values[:];bad[i]=x;assert not run('ekqt',bad,mm);cases+=1
            unknowns(lambda model:run('ekqt',values,model),mm,('ekqs','zc6','sjd','soy','sca'))
    # Native individual quantifiers: every counterpart, every same-event pair.
    records={('p','p','p','p','p','case'),('p','p','p','q','q','case'),('p','q','q','q','p','case'),('p','q','q','p','q','case')}
    good={('p','p','p','p','q','case',Q(5),Q(3)),('p','q','q','q','p','case',Q(5),Q(3))}
    constant=FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:c(0)))
    pop=FunctionValue(('individual',),'truth',lambda p:True)
    expected=norm(['p','p','case','p','q',c(0),c(2),pop,constant,constant,constant,c(3)])
    aliases={'ra':'p','zbm':'q','ta':'p','rb':'q','yn':'p','yo':'q','yp':'p','zc7':'q'}
    mm=m|{n:lambda x=x:x for n,x in aliases.items()}|{'eirh':lambda b,p,ctx:b=='p' and ctx=='case','eislu':lambda *xs:constant,'ekqr':lambda *xs:xs==('p','q','case'),'eje7':lambda *xs:xs==('p','p','case'),'eipf':lambda *xs:norm(xs)==expected,'eje6':lambda *xs:xs in records,'ekqt':lambda *xs:norm(xs) in good}
    values=['p',c(5),c(3),'case'];check=lambda model:run('ekqu',values,model,domain=('p','q'))
    assert check(mm);cases+=1
    for row in list(records):
        records.remove(row);assert not check(mm);cases+=1;records.add(row)
    extra=('p','p','p','q','p','case');records.add(extra);assert not check(mm);cases+=1;records.remove(extra)
    for row in list(good):
        good.remove(row);assert not check(mm);cases+=1;good.add(row)
    for n in ('ekqr','eje7','eipf'):
        assert not check(mm|{n:lambda *xs:False});cases+=1
    unknowns(check,mm,('ekqr','eje7','eipf','eje6','ekqt'))
    return dict(cases=cases,both_frames_all_four_coordinates_and_same_event_identity=True,zero_and_signed_speed_maps_checked=True,every_counterpart_and_all_record_pairs_required=True,finite_record_routes_not_a_complete_material_continuum=True)

@lru_cache(None)
def patch_checks():
    cuts,m,pos,members,family,hist,norm=environment();c,r=cuts.make,cuts.read;cases=0;bounds=(-1,1,-2,2)
    assert r(run('ekqv',list(map(c,bounds)),m))==8;cases+=1
    for xyz,expected in (((0,0,0,1),True),((0,-1,-2,0),True),((0,1,2,2),True),((1,0,0,1),False),((0,2,0,1),False),((0,0,3,1),False)):
        region=run('ekqy',list(map(c,bounds)),m);assert region(*map(c,xyz))==expected;cases+=1
    for i in range(2):
        bad=list(bounds);bad[2*i+1]=bad[2*i];assert not run('ekqw',list(map(c,bad)),m);cases+=1
        bad[2*i+1]-=1;assert not run('ekqw',list(map(c,bad)),m);cases+=1
    expected=norm(hist('patch','k'));mm=m|{'ekqr':lambda *xs:xs==('body','k','case'),'eiad':lambda *xs:norm(xs)==expected}
    values=['body','patch','k','case',*map(c,bounds)];assert run('ekqz',values+[c(1)],mm,'instance');cases+=1
    # Isolate material selection from the abstract whole-history gate.
    for p in ('p','q'):
        members['patch'].symmetric_difference_update({p});assert not run('ekqz',values+[c(1)],mm|{'eiad':lambda *xs:True},'instance');cases+=1;members['patch'].symmetric_difference_update({p})
    for axis in range(3):
        old=pos['patch']['p'];changed=list(old);changed[axis]+=1;pos['patch']['p']=tuple(changed)
        assert not run('ekqz',values+[c(1)],mm|{'eiad':lambda *xs:True},'instance');cases+=1;pos['patch']['p']=old
    for i,x in enumerate(('patch','body','K','other')):
        bad=values[:];bad[i]=x;assert not run('ekqz',bad+[c(1)],mm,'instance');cases+=1
    assert run('ekqz',values+[c(3)],mm,'instance');cases+=1
    refused(lambda:run('ekqz',values,mm));cases+=1
    unknowns(lambda model:run('ekqz',values+[c(1)],model,'instance'),mm,('ekqr','eiad','eirh','eislu','eisls','eislt','sca'))
    return dict(cases=cases,proper_nonempty_rectangular_material_patch=True,all_three_coordinates_share_same_member_and_time=True,normal_displacement_and_tangential_limits_distinguished=True,area_uses_both_positive_transverse_widths=True)

def force_curve(cuts,slope=2,offset=3):
    c,r=cuts.make,cuts.read
    return FunctionValue((RS,),PS,lambda time:FunctionValue(('individual',),RS,lambda axis:c(slope*r(time)+offset if axis=='x' else 17-r(time) if axis=='y' else -11 if axis=='z' else 0)))

@lru_cache(None)
def pressure_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    for a,b,lo,hi,bounds in ((0,48,0,2,(-1,1,-2,2)),(2,3,-1,3,(0,2,0,5)),(-3,-4,0,2,(-1,1,-2,2)),(0,0,0,4,(0,3,0,2))):
        area=Q((bounds[1]-bounds[0])*(bounds[3]-bounds[2]));integral=Q(a,2)*(hi*hi-lo*lo)+b*(hi-lo);pressure=integral/(area*(hi-lo));force=force_curve(cuts,a,b)
        mm=m|{'sede':lambda lower,upper,profile,value:r(lower)==lo and r(upper)==hi and r(value)==integral and all(r(profile(c(t)))==a*t+b for t in (-1,0,1,2,3))}
        values=[force,*map(c,(lo,hi,*bounds,pressure))];assert run('ekq3',values,mm);cases+=1
        for i in range(1,len(values)):
            bad=values[:];bad[i]=c(r(bad[i])+Q(1,7));assert not run('ekq3',bad,mm) or (integral==0 and i in (3,4,5,6)),(a,b,i);cases+=1
        for axis in ('x','y','z'):
            profile=run('ekq2',[force,axis],m)
            for t in (-1,0,1,2):assert r(profile(c(t)))==(a*t+b if axis=='x' else 17-t if axis=='y' else -11);cases+=1
        for i,j in ((1,2),(3,4),(5,6)):
            bad=values[:];bad[j]=bad[i];assert not run('ekq3',bad,mm);cases+=1
        unknowns(lambda model:run('ekq3',values,model),mm,('sede','ba','bg','shv'))
    # The stationary example has positive pressure 6 even though P*v=0.
    assert Q(48,8)==6 and 6*0==0;cases+=1
    deps={d['name'] for d in extract_document(core(),roots=['ekq3'],statement_indices=[]).document['declarations']}
    assert not deps&{'sekm','sekl','seki','seko'}
    return dict(cases=cases,mean_normal_force_over_same_positive_area_and_duration=True,signed_zero_and_nonconstant_force_histories=True,tangential_force_not_forced_to_zero=True,no_division_by_mirror_velocity_or_work_balance=True,integral_boundary_diagnostics_not_general_integration_proof=True)

@lru_cache(None)
def setting_question_checks():
    cuts,m,pos,members,family,hist,norm=environment();c=cuts.make;cases=0;force=force_curve(cuts)
    by=dict(body='body',patch='patch',process='process',frame='K',forceunit='forceunit',scope='scope',context='case',light=c(5),speed=c(3),lower=c(0),upper=c(2),ylower=c(-1),yupper=c(1),zlower=c(-2),zupper=c(2),force=force)
    values=[by[n] for n,t in SETTING]
    def models(frame):
        row=by|dict(frame=frame,lengthunit='length',timeunit='duration')
        rows={'ekqu':norm([row[n] for n,t in PLANE]),'ekqz':norm([row['body'],row['patch'],'k',row['context'],*[row[n] for n,t in BOUNDS]]),'eisub':norm([row[n] for n,t in FORCE_MODEL])}
        return m|{n:lambda *xs,row=row:norm(xs)==row for n,row in rows.items()}
    for frame in ('K','k'):
        values[3]=frame;mm=models(frame);assert run('ekq4',values,mm);cases+=1
        for i,(n,t) in enumerate(SETTING):
            bad=values[:];bad[i]=force_curve(cuts,9,13) if n=='force' else c(cuts.read(bad[i])+Q(1,7)) if t==R else 'other'
            assert not run('ekq4',bad,mm),(i,n);cases+=1
        for n in ('ekqu','ekqz','eisub'):assert not run('ekq4',values,mm|{n:lambda *xs:False});cases+=1
        unknowns(lambda model:run('ekq4',values,model),mm,('ekqu','ekqz','eisub','eisls','eislt'))
    values[3]='K';target=norm(values)
    candidate_model=m|{'ekq4':lambda *xs:norm(xs)==target,'sede':lambda lo,hi,profile,total:cuts.read(lo)==0 and cuts.read(hi)==2 and cuts.read(total)==10 and all(cuts.read(profile(c(t)))==2*t+3 for t in (0,1,2))}
    assert run('ekq5',values+[c(Q(5,8))],candidate_model);cases+=1
    assert not run('ekq5',values+[c(1)],candidate_model);cases+=1
    assert not run('ekq5',values+[c(Q(5,8))],candidate_model|{'ekq4':lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekq5',values+[c(Q(5,8))],model),candidate_model,('ekq4','sede'))
    for accepted in (set(),{Q(2)},{Q(-3),Q(2)}):
        model={'ekq5':lambda *xs:norm(xs[:-1])==target and cuts.read(xs[-1]) in accepted}
        question=run('ekq6',values,model);assert isinstance(question,QuestionValue);cases+=1
        for p in (-3,0,2,5):assert question.function(c(p))==(Q(p) in accepted);cases+=1
        for i,(n,t) in enumerate(SETTING):
            bad=values[:];bad[i]=force_curve(cuts,9,13) if n=='force' else c(cuts.read(bad[i])+Q(1,7)) if t==R else 'other'
            altered=run('ekq6',bad,model);assert not altered.function(c(2));cases+=1
    question=run('ekq6',values,{'ekq5':forbidden})
    try:question.function(c(2))
    except ValueError as exc:assert 'Unknown' in str(exc)
    else:raise AssertionError('Unknown pressure candidate accepted')
    cases+=1
    return dict(cases=cases,same_physical_plane_patch_process_frame_units_and_force_history=True,rest_and_lab_frames_both_supported=True,all_setting_roles_captured_before_answer=True,empty_single_multiple_answer_questions_allowed=True,question_construction_does_not_execute_candidates=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));unit=inv['units'][214];math=next(m for m in inv['math'] if m['id']=='M0368')
    assert unit['id']=='einstein-1905:u0215' and unit['math_ids']==['M0368'];assert digest(unit['text'].encode('utf-8'))==unit['text_sha256']
    return dict(status='material_surface_and_mean_pressure_dependencies_not_source_completion',unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],math=dict(id=math['id'],sha256=math['sha256'],reading='ξ=0'),observations=LIMITS,verified_full_units=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==394
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/stationary-mirror-boundary-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps={d['name'] for d in extract_document(new.document,roots=['ekq6'],statement_indices=[]).document['declarations']}
    assert {'eirh','eje2','eje6','eje7','eigy','eiah','ekce','sejm','sejn','sede','eisub'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz','sekm'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,all_394_statements_and_judgments_preserved=True,no_new_source_completion_claim=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('plane',plane_checks),('mapping',mapping_checks),('patch',patch_checks),('pressure',pressure_checks),('setting_question',setting_question_checks),('structure',structure_checks)]}
    helpers=('compose_stationary_mirror_boundary','compose_solid_sphere_geometry','compose_material_body_motion','compose_rod_methods','compose_field_transformation_application','compose_field_equations','compose_material_relative_frame','compose_doppler_infinity','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_translated_light_trial','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_mirror_surface_pressure.py','scripts/check_mirror_surface_pressure.py','tests/test_mirror_surface_pressure.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='material_plane_two_frame_patch_and_mean_pressure_dependencies_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
