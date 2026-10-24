"""Check a fixed physical setting, energy candidates, questions and gloss roles."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,Content,QuestionValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM
from scripts.check_light_region_slices import setup
from scripts.check_same_light_portion import CONSTANTS as PRIOR_CONSTANTS,DOMAIN as PRIOR_DOMAIN
from scripts.check_wave_cycle_frequency import refused
from scripts.compose_portion_energy_inquiry import *
from scripts.read_portion_energy_inquiry import DOC,SOURCE,INVENTORY,READING,PRIOR,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'eistt':'energyquestion'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values(),*[n for n,t in SETTING if t=='a']]))
DEPENDENCIES=('reports/same-light-portion-v1.json','reports/mean-light-energy-v1.json','reports/light-region-slices-v1.json')
BOUNDS={'ekn6':{'eklp','eklg','eklh','ekl4','ekme'},'ekn7':{'ekn6','eknw'},'ekoa':{'ekn7','sede'},'ekob':{'ekoa'},'ekoc':{'ekoa'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ekod','ekoe','ekof','ekoh'):bounds|={'eknz','ekn7','ekob','ekoc','ekod','ekoe','ekog'}-{name}
    if mode=='integral':bounds.discard('sede')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpei'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jpeicapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jpeicapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native'):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jpeicapture']=capture
    result=evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def gate(xs,ys,slots,cuts):return len(xs)==len(ys) and all(same_value(x,y,s,cuts) for x,y,(_,s) in zip(xs,ys,slots))

def setting(cuts,root='ekn6'):
    c=cuts.make;slots=fixture(root)[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))];pos={n:i for i,(n,t) in enumerate(SETTING)}
    for n,x in dict(light=5,speed=3,ax=0,ay=1,az=0,ex=0,ey=0,ez=5,hx=5,hy=0,hz=0,rate=Q(1,5),radius=2,pi=Q(3,4),amplitude=5,newamplitude=Q(25,4),coefficient=Q(5,3),volume=8,newvolume=Q(32,5)).items():values[pos[n]]=c(x)
    for n,s in [('frame','ra'),('scope','eisrx'),('portion','zvaa')]:values[pos[n]]=CONSTANTS[s]
    return values,pos

def flatten(node):
    return sum((flatten(a) for a in node['arguments']),[]) if node['kind']=='and' else [node]

@lru_cache(None)
def setting_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;values,pos=setting(cuts);slots=fixture('ekn6')[1];cases=0
    # Exact AST comparison to the six previously checked physical conditions.
    parent=parse(read(PARENT));ds={d['name']:d for d in parent['declarations']};old=flatten(ds['ekmi']['body'])
    new=next(d for d in core()['declarations'] if d['name']=='ekn6')
    projected=deepcopy(ds['ekmi']);projected['parameters']=projected['parameters'][:-2]
    terms=[x for x in old if x.get('symbol')!='ekmg'];body=terms[0]
    for term in terms[1:]:body=dict(kind='and',arguments=[body,term])
    projected['body']=body
    parent['declarations']=[projected if d['name']=='ekmi' else d for d in parent['declarations']]
    # Recanonicalize bound names after removing two parameters. No free-role rename.
    parent['statements']=[]
    parent['declarations']=parent['declarations'][:next(i for i,d in enumerate(parent['declarations']) if d['name']=='ekmi')+1]
    projected=parse(format_graph(parent,'compact'))['declarations'][-1]
    assert flatten(new['body'])==flatten(projected['body']);cases+=1
    assert new['parameters']==projected['parameters'];cases+=1
    names=('eklp','eklg','eklh','ekl4','ekme');seen={n:[] for n in names}
    captures={n:(lambda *xs,n=n:seen[n].append(xs) or True) for n in names}
    assert run('ekn6',values,m|captures);cases+=1
    assert {n:len(rows) for n,rows in seen.items()}==dict(eklp=1,eklg=1,eklh=1,ekl4=1,ekme=2);cases+=1
    for name in ('eklp','eklg','eklh'):assert gate(seen[name][0],values[:len(BASE)],slots[:len(BASE)],cuts);cases+=1
    fp={n:i for i,(n,t) in enumerate(FRAME)}
    for row,frame,amps,rho in zip(seen['ekme'],(CONSTANTS['ra'],CONSTANTS['zbm']),((0,0,5,5,0,0),(0,0,Q(25,4),5,Q(15,4),0)),(Q(25,6),Q(625,96))):
        assert row[fp['frame']]==frame and row[fp['scope']]=='section8' and row[fp['portion']]==CONSTANTS['zvaa'];cases+=1
        assert tuple(r(row[fp[n]]) for n in ('ex','ey','ez','hx','hy','hz'))==amps;cases+=1
        assert r(row[fp['time']])==0 and r(row[fp['density']])==rho;cases+=1
        for point in ((0,0,0,0),(1,2,3,4)):
            x,y,z,t=map(Q,point);old=(Q(5,4)*(x+3*t),y,z,Q(5,4)*(t+3*x/25)) if frame==CONSTANTS['zbm'] else (x,y,z,t)
            assert r(row[fp['phase']](*map(c,point)))==Q(1,5)*(old[3]-old[1]/5);cases+=1
            assert row[fp['portionregion']](*map(c,point))==(sum((a-b*5*old[3])**2 for a,b in zip(old[:3],(0,1,0)))<=4);cases+=1
    decl={d['name']:d for d in fixture('ekn6')[0]['declarations']};sorts={n:[('',s) for s in decl[n]['parameters']] for n in names}
    models={n:(lambda *xs,n=n:any(gate(xs,row,sorts[n],cuts) for row in seen[n])) for n in names}
    assert run('ekn6',values,m|models);cases+=1
    for i,(_,sort) in enumerate(slots):
        if SETTING[i][0] in ('light','speed'):continue
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekn6',bad,m|models),(i,SETTING[i]);cases+=1
    for name in names:assert not run('ekn6',values,m|models|{name:lambda *xs:False});cases+=1
    unknowns(lambda mm:run('ekn6',values,mm),m|models,names)
    return dict(cases=cases,exact_prior_physical_conditions_without_total_energy_witnesses=True,old_and_new_mean_models_share_same_portion=True,all_68_roles_retained=True)

@lru_cache(None)
def identity_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;values,pos=setting(cuts,'ekn7');slots=fixture('ekn7')[1];cases=0
    row=[CONSTANTS['eistk'] if n=='scope' else values[pos[n]] for n,t in TRANSPORT_FRAME]
    sorts=[slots[pos[n]] for n,t in TRANSPORT_FRAME]
    models={'ekn6':lambda *xs:gate(xs,values,slots,cuts),'eknw':lambda *xs:gate(xs,row,sorts,cuts),'tc':lambda:c(5)}
    mm=m|models;assert run('ekn7',values,mm);cases+=1
    for i,(_,sort) in enumerate(slots):
        bad=values[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekn7',bad,mm),(i,SETTING[i]);cases+=1
    for name in ('ekn6','eknw'):assert not run('ekn7',values,mm|{name:lambda *xs:False});cases+=1
    for name in ('ra','eisrx','zvaa'):assert not run('ekn7',values,mm|{name:lambda:'other'});cases+=1
    assert not run('ekn7',values,mm|{'tc':lambda:c(6)});cases+=1
    for amp in (0,-1):
        bad=values[:];bad[pos['amplitude']]=c(amp);assert not run('ekn7',bad,mm|{'ekn6':lambda *xs:True,'eknw':lambda *xs:True});cases+=1
    unknowns(lambda mm:run('ekn7',values,mm),mm,('ekn6','eknw','tc'))
    return dict(cases=cases,all_68_setting_roles_shared=True,same_initial_portion_and_section_scope=True,no_energy_value_in_setting=True)

@lru_cache(None)
def candidate_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;values,pos=setting(cuts,'ekoa');slots=fixture('ekoa')[1][:-1];cases=0
    # Rational pi is a diagnostic, not the manuscript integral definition.
    for direction,D in ((0,Q(5,4)),(Q(1,3),Q(1)),(1,Q(1,2))):
        for amplitude in (Q(0),Q(25,4)):
            current=values[:];current[pos['ax']]=c(direction);current[pos['newamplitude']]=c(amplitude)
            pi=Q(3,4);radius=Q(2);rho=amplitude*amplitude/(8*pi);volume=Q(4,3)*pi*radius**3/D;energy=rho*volume
            current[pos['newvolume']]=c(volume)
            def integral(lo,hi,f,value):
                samples=tuple(r(f(c(x))) for x in (0,Q(1,3),1))
                return (r(lo),r(hi))==(-radius/D,radius/D) and any(samples==tuple(weight*pi*(radius**2-D*D*x*x) for x in (0,Q(1,3),1)) and r(value)==weight*volume for weight in (Q(1),rho))
            mm=m|{'ekn7':lambda *xs:gate(xs,current,slots,cuts),'sedi':lambda p:r(p)==pi,'sede':integral}
            for answer in (energy,energy+1,-1):assert run('ekoa',current+[c(answer)],mm)==(answer==energy);cases+=1
            for i,(_,sort) in enumerate(slots):
                # Keep arithmetic inputs in a valid rational boost domain; all other slots are perturbed.
                if SETTING[i][0] in ('light','speed','pi'):continue
                bad=current[:];bad[i]=sentinel(sort,100+i,cuts);assert not run('ekoa',bad+[c(energy)],mm),(i,SETTING[i]);cases+=1
            assert not run('ekoa',current+[c(energy)],mm|{'ekn7':lambda *xs:False});cases+=1
            assert not run('ekoa',current+[c(energy)],mm|{'sede':lambda *xs:False});cases+=1
            unknowns(lambda mod:run('ekoa',current+[c(energy)],mod),mm,('ekn7','sede','sedi','shv'))
    refused(lambda:run('ekoa',current+[c(energy)],mm,'integral'));cases+=1
    return dict(cases=cases,actual_weighted_new_frame_slice_integral_checked=True,zero_single_and_wrong_energy_candidates_distinguished=True,same_setting_outside_candidate=True,native_unbounded_integral_refused=True)

@lru_cache(None)
def question_checks():
    cuts,m=setup();c,r=cuts.make,cuts.read;values,pos=setting(cuts,'ekob');slots=fixture('ekob')[1];cases=0
    for accepted in (set(),{Q(2)},{Q(2),Q(3)}):
        def candidate(*xs):return gate(xs[:-1],values,slots,cuts) and r(xs[-1]) in accepted
        mm={'ekoa':candidate}
        questions=[run(name,values,mm) for name in ('ekob','ekoc')]
        for question in questions:
            assert isinstance(question,QuestionValue);cases+=1
            for value in (0,2,3,4):assert question.function(c(value))==(Q(value) in accepted);cases+=1
        # A different fixed context cannot select a new witness for this answer.
        for i,(_,sort) in enumerate(slots):
            bad=values[:];bad[i]=sentinel(sort,100+i,cuts);question=run('ekob',bad,mm)
            assert not question.function(c(2)),(i,SETTING[i]);cases+=1
        question=run('ekob',values,{'ekoa':forbidden})
        try:question.function(c(2))
        except ValueError as e:assert 'Unknown clock-site-time' in str(e)
        else:raise AssertionError('Unknown candidate accepted')
        cases+=1
    return dict(cases=cases,empty_single_and_multiple_answer_questions_allowed=True,all_setting_roles_captured_before_candidate=True,gloss_is_the_same_question=True,construction_does_not_evaluate_candidates=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    for name,question in [('ekod','ekob'),('ekoe','ekoc')]:
        rows={'eists':{('energyquestion','author','enclosureclause','eknz','ekn7',question,'section8','case')}}
        mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run(name,[],model),mm,rows)
        assert run(name,[],mm|{'ekn7':forbidden,question:forbidden,'eknz':forbidden});cases+=1
    rows={'eisme':{('energyquestion','author','ekod','ekoe','paper','case')},'eisra':{('energyquestion','author','paper','enclosureclause','eknz','ekod','section8','case')}}
    mm={n:relation(rs) for n,rs in rows.items()}|{'ekod':lambda:Content(('case','other'),(True,True))}
    cases+=perturb(lambda model:run('ekof',[],model),mm,rows)
    assert not run('ekof',[],mm|{'ekod':lambda:Content(('case','other'),(False,False))});cases+=1
    assert run('ekof',[],mm|{'ekoe':forbidden});cases+=1
    unknowns(lambda model:run('ekof',[],model),mm,('ekod',))
    rows={'eir3':{('energyquestion','author','paper','ekog','case')},'ue':{('enclosuresentence','energyquestion','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda model:run('ekoh',[],model),mm,rows)
    assert not run('ekoh',[],{n:lambda *xs:True for n in rows}|{'eistt':lambda:'enclosuresentence'});cases+=1
    return dict(cases=cases,closed_condition_and_question_rules_not_executed=True,one_question_act_and_explanatory_gloss=True,back_reference_and_author_order_preserved=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==390 and new.document['statements'][:389]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[388])==selection_binding(old,[388])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/same-light-portion-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names=set(selection_binding(new,[INDEX])['dependencies'])
    assert set(MEANINGS)|{'eistj','eiste','eistm','eisme','eists','eisra','eknw','sede'}<=names
    # Historical ungrounded question and actual energy ratio are not dependencies.
    assert not {'sehb','sehd','zvaf','zvag','ekml','sech','ekl6'}&names
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['selection']==selection_binding(new,[INDEX]) and reading['reviewed_math_elements']==2
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_reference_individuals=1,all_389_statements_and_judgments_preserved=True,reviewed_prose_characters=reading['reviewed_prose_characters'],reviewed_math_elements=2)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('setting',setting_checks),('identity',identity_checks),('candidate',candidate_checks),('question',question_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_mean_light_energy','compose_moving_ball_transport','compose_wave_transform_application','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_light_region_slices','check_same_light_portion','check_wave_cycle_frequency','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{DOC,SOURCE,INVENTORY,READING,*DEPENDENCIES,'scripts/compose_portion_energy_inquiry.py','scripts/check_portion_energy_inquiry.py','scripts/read_portion_energy_inquiry.py','tests/test_portion_energy_inquiry.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='same_portion_moving_frame_mean_energy_question_and_gloss_checked',document=FULL,**results,alignment=dict(unit='einstein-1905:u0205',range=[108,272],statements=[INDEX]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
