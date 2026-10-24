"""Check receding directions, quantifier order, spatial angles and the printed law."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from math import isqrt
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_wave_inquiry import arithmetic_model
from scripts.check_wave_transform_application import DOMAIN,CONSTANTS
from scripts.check_wave_cycle_frequency import refused
from scripts.check_resting_charge_force import retag
from scripts.check_velocity_angle_measure import branch_model
from scripts.compose_observed_doppler import *
from noema.finite_semantics import FunctionValue
from scripts.check_distant_direction_geometry import arithmetic
from scripts.check_clock_site_time import relation,perturb
import re

CONSTANTS=CONSTANTS|{'eissm':'claim','eissn':'dopplerdisplay','eisso':'angular'}
DOMAIN=tuple(dict.fromkeys([*DOMAIN,*CONSTANTS.values()]))

DOC='docs/observed-doppler-v1.md';SOURCE='data/einstein-observed-doppler-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp-p911-0.jpg'
DEPENDENCIES=('reports/distant-direction-geometry-v1.json','reports/wave-cycle-frequency-v1.json','reports/wave-transform-application-v1.json','reports/distant-wave-source-v1.json','reports/wave-inquiry-v1.json')
BOUNDS={'ekd2':{'ekc7'},'ekd3':{'ekdm','ekd2'},'ekd4':{'ekdc','ekc7'},'ekd6':{'eivu','ekdc','ekd5'},'ekd7':{'ekcl','ekd3','ekd4','ekd6','ekdq','s6f'},'ekeb':{'ekd7','ekea'},'ekec':{'ekcl'}}

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','sjd','sje','szi','soy','sky','shu'}
    if mode!='full':bounds|=BOUNDS.get(name,set())|{'ejor','sedi'}
    if mode=='quantified':bounds.add('seag')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='pointwise':
        found=[]
        def expose(node):
            if isinstance(node,list):return [expose(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and node['sort']==RS:
                found.append(dict(name=node['variable'],sort=RS));return expose(node['body'])
            return {k:expose(x) for k,x in node.items()}
        d['body']=expose(d['body']);assert len(found)==1;d['parameters']+=found
    if mode=='quantified':
        def replace(node):
            if node==RS:return 'individual'
            if isinstance(node,list):return [replace(x) for x in node]
            if isinstance(node,dict):return {k:replace(x) for k,x in node.items()}
            return node
        doc=replace(doc);d=next(d for d in doc['declarations'] if d['name']==name)
    if mode.startswith('slot:'):
        doc=retag(doc)
        for dec in doc['declarations']:
            if dec['kind']=='primitive':
                dec['parameters']=['individual' if isinstance(t,dict) else t for t in dec['parameters']]
                if isinstance(dec['result'],dict):dec['result']='individual'
            else:
                for p in dec['parameters']:
                    if isinstance(p['sort'],dict):p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name)
        pivot=int(mode.split(':')[1]);node=d['body']['body'];retained=None
        for i in range(len(VARIABLES)):
            assert node['kind']=='forall'
            if i==pivot:retained={k:node[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
            node=node['body']
        d['body']['body']=retained|{'body':node}
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jodp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jodpcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jodpcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(value):captured.append(value);return True
    mm['jodpcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def function(cuts,fn):return FunctionValue((RS,),RS,lambda t:cuts.make(fn(cuts.read(t))))

@lru_cache(None)
def model_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    for n in ((1,0,0),(Q(3,5),Q(4,5),0),(0,0,-1)):
        family=run('ekdv',list(map(c,n)),m);phases=run('ekdw',list(map(c,(5,2,*n))),m)
        for distance,time in product((1,5,20),(-2,0,3)):
            point=family(c(distance))(c(time))
            assert tuple(r(point(a)) for a in ('x','y','z','t'))==(*(-distance*a for a in n),time);cases+=1
            assert r(phases(c(distance))(c(time)))==2*(Q(time)+Q(distance,5));cases+=1
    xyz=[function(cuts,lambda t:3*t+1),function(cuts,lambda t:Q(2)),function(cuts,lambda t:Q(-1))]
    obs=run('ekdx',xyz,m)
    phase=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)-r(x)+3*r(y)-r(z)))
    received=run('ekdy',[phase,*xyz],m)
    for distance,time in product((1,10),(-1,0,2)):
        point=obs(c(distance))(c(time));assert tuple(r(point(a)) for a in ('x','y','z','t'))==(3*time+1,2,-1,time);cases+=1
        assert r(received(c(distance))(c(time)))==6-time;cases+=1
    domain=run('ekdz',[],m)
    for distance in (-2,0,Q(1,3),10):assert domain(c(distance))==(distance>0);cases+=1
    unknowns(lambda mm:run('ekdw',list(map(c,(5,2,1,0,0))),mm)(c(5))(c(2)),m,('shv','sjd','szi'))
    return dict(cases=cases,static_source_curves_and_phase_offsets=True,same_observer_path_in_every_model=True)

@lru_cache(None)
def mapping_checks():
    cuts,m=arithmetic();c=cuts.make;cases=0
    # xi=1, eta=2, zeta=-1, gamma=5/4; inverse t=gamma*(tau+3/25).
    old=[function(cuts,lambda t:3*t+Q(4,5)),function(cuts,lambda t:Q(2)),function(cuts,lambda t:Q(-1))]
    new=[function(cuts,lambda t:Q(1)),function(cuts,lambda t:Q(2)),function(cuts,lambda t:Q(-1))]
    for time in (0,Q(1,2),1,2):
        oldtime=Q(5,4)*(time+Q(3,25));values=[c(5),c(3),c(0),c(3),*old,*new,c(time)]
        assert run('ekd5',values,m);cases+=1
        for i in range(4,10):
            changed=values[:];changed[i]=function(cuts,lambda t:Q(77));assert not run('ekd5',changed,m);cases+=1
        for lower,upper,expected in ((oldtime,3,True),(0,oldtime,True),(oldtime+Q(1,10),3,False),(0,oldtime-Q(1,10),False)):
            changed=values[:];changed[2:4]=[c(lower),c(upper)];assert run('ekd5',changed,m)==expected;cases+=1
    unknowns(lambda mm:run('ekd5',values,mm),m,('soy','shv','bf'))
    return dict(cases=cases,inverse_lorentz_time_and_three_positions_checked=True,closed_old_interval_checked=True)

@lru_cache(None)
def physical_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;cases=0
    harmonic=[function(cuts,lambda t:t),function(cuts,lambda t:t+1),c(4),c(8)]
    # Diagnostic profiles are not asserted to be sine/cosine; ekc7 is the boundary.
    for distance in (Q(-1),Q(0),Q(1),Q(5),Q(20)):
        values=harmonic+list(map(c,(5,2,Q(3,5),Q(4,5),0,4,Q(1,4),distance)))
        expected=harmonic+[c(2),c(2*distance/5),c(4),c(Q(1,4))]
        sorts=[s for _,s in fixture('ekd2')[1]][:4]+[RS]*4
        gate=lambda *xs:all(same_value(x,y,s,cuts) for x,y,s in zip(xs,expected,sorts))
        mm=m|{'ekc7':gate}
        assert run('ekd2',values,mm)==(distance>0);cases+=1
        if distance>0:
            assert not run('ekd2',values,mm|{'ekc7':lambda *xs:False});cases+=1
    phase=FunctionValue((RS,)*4,RS,lambda x,y,z,t:c(2*r(t)+1))
    xyz=[function(cuts,lambda t:Q(1)),function(cuts,lambda t:Q(2)),function(cuts,lambda t:Q(-1))]
    def model_fingerprint(fn):return tuple(r(fn(c(d))(c(t))(a)) for d in (1,5) for t in (0,2) for a in ('x','y','z','t'))
    def phase_fingerprint(fn):return tuple(r(fn(c(d))(c(t))) for d in (1,5) for t in (0,2))
    def domain_fingerprint(fn):return tuple(fn(c(d)) for d in (-1,0,1,5))
    for root,fields,values,model_name,phase_name in (
        ('ekd3',SOURCE_FIELDS,['source','wave','process','frame','lengthunit','timeunit','scope','case',*harmonic,*map(c,(5,2,Q(3,5),Q(4,5),0,4,Q(1,4),0,2))],'ekdv','ekdw'),
        ('ekd4',RECEIVER,['observer','wave','process','moving','lengthunit','timeunit','scope','case',*harmonic,phase,*xyz,*map(c,(2,1,4,Q(1,4),0,2))],'ekdx','ekdy')):
        source=root=='ekd3';by=dict(zip([n for n,t in fields],values));subject=by['source' if source else 'observer']
        fm=run(model_name,list(map(c,(Q(3,5),Q(4,5),0))) if source else xyz,m)
        fp=run(phase_name,list(map(c,(5,2,Q(3,5),Q(4,5),0))) if source else [phase,*xyz],m)
        expected_model=(subject,by['frame'],'lengthunit','timeunit',model_fingerprint(fm),(False,False,True,True),'scope','case')
        expected_phase=(subject,'wave','process',by['frame'],'lengthunit','timeunit',model_fingerprint(fm),phase_fingerprint(fp),(False,False,True,True),Q(0),Q(2),not source,'scope','case')
        def model_norm(xs):return (*xs[:4],model_fingerprint(xs[4]),domain_fingerprint(xs[5]),*xs[6:])
        def phase_norm(xs):return (*xs[:6],model_fingerprint(xs[6]),phase_fingerprint(xs[7]),domain_fingerprint(xs[8]),r(xs[9]),r(xs[10]),*xs[11:])
        mm=m|{'eissk':lambda *xs:model_norm(xs)==expected_model,'eissl':lambda *xs:phase_norm(xs)==expected_phase,'ekdm':lambda *xs:tuple(map(r,xs))==(Q(3,5),Q(4,5),Q(0)),'ekd2':lambda *xs:True,'ekdc':lambda *xs:True,'ekc7':lambda *xs:True}
        mode='pointwise' if source else 'native';extra=[c(5)] if source else []
        assert run(root,values+extra,mm,mode);cases+=1
        for gate in ('eissk','eissl',*(['ekdm','ekd2'] if source else ['ekdc','ekc7'])):
            assert not run(root,values+extra,mm|{gate:lambda *xs:False},mode);cases+=1
        for i in (0,1,2,3,4,5,6):
            changed=values[:];changed[i]='other';assert not run(root,changed+extra,mm,mode);cases+=1
        for gate,expected,norm in (('eissk',expected_model,model_norm),('eissl',expected_phase,phase_norm)):
            for i in range(len(expected)):
                bad=expected[:i]+('wrong',)+expected[i+1:]
                assert not run(root,values+extra,mm|{gate:lambda *xs,bad=bad,norm=norm:norm(xs)==bad},mode);cases+=1
        unknowns(lambda model:run(root,values+extra,model,mode),mm,('eissk','eissl'))
        if source:
            assert run(root,values+[c(-1)],mm|{'ekd2':lambda *xs:False},mode);cases+=1
            refused(lambda:run(root,values,mm))
    return dict(cases=cases,same_subject_wave_process_frames_units_and_phase_roles_checked=True,emitted_and_received_roles_distinct=True,period_boundary_not_claimed_as_measured_sine=True)

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;slots=fixture('ekd7')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(SETTING,slots))]
    pos={n:i for i,(n,t) in enumerate(SETTING)}
    fixed=dict(light=5,rate=2,ax=Q(3,5),ay=Q(4,5),az=0,pi=4,cycle=8,oldperiod=4,newperiod=5,frequency=Q(1,4),newfrequency=Q(1,5),anglecos=Q(3,5),anglesin=Q(4,5),ratio=Q(4,3),principal=1,angle=1,obslower=0,obsupper=2,oldobslower=0,oldobsupper=3)
    for n,x in fixed.items():values[pos[n]]=c(x)
    by=dict(zip([n for n,t in SETTING],values));sortby=dict(zip([n for n,t in SETTING],[s for _,s in slots]))
    shifted=FunctionValue((RS,)*4,RS,lambda *xs:c(19))
    def matches(xs,expected,sorts):return len(xs)==len(expected) and all(same_value(x,y,s,cuts) for x,y,s in zip(xs,expected,sorts))
    def expected(fields,overrides=None):return [(overrides or {}).get(n,by.get(n)) for n,t in fields]
    parent=values[:len(FAMILY)];parent_sorts=[s for _,s in slots[:len(FAMILY)]]
    source=expected(SOURCE_FIELDS,{'period':by['oldperiod']});ss=[s for _,s in fixture('ekd3')[1]]
    receiver=expected(RECEIVER,dict(frame=CONSTANTS['zbm'],phase=shifted,x=by['obsx'],y=by['obsy'],z=by['obsz'],rate=c(Q(8,5)),offset=by['newoffset'],period=by['newperiod'],frequency=by['newfrequency'],lower=by['obslower'],upper=by['obsupper']));rs=[s for _,s in fixture('ekd4')[1]]
    angle=[c(x) for x in (Q(3,5),Q(4,5),0,3,Q(3,5),Q(4,5),Q(4,3),1,4,1)]
    mm=m|{'soy':lambda *xs:c(Q(5,4)),'zb7':lambda:c(3),'s6f':lambda *xs:shifted,'ekcl':lambda *xs:matches(xs,parent,parent_sorts),'ekd3':lambda *xs:matches(xs,source,ss),'ekd4':lambda *xs:matches(xs,receiver,rs),'ekd6':lambda *xs:matches(xs,values,[s for _,s in slots]),'ekdq':lambda *xs:tuple(map(r,xs))==tuple(map(r,angle))}
    assert run('ekd7',values,mm);cases=1
    for i,(n,s) in enumerate(slots):
        changed=values[:];changed[i]=sentinel(s,100+i,cuts);assert not run('ekd7',changed,mm),(i,SETTING[i]);cases+=1
    for name in ('ekcl','ekd3','ekd4','ekd6','ekdq'):
        assert not run('ekd7',values,mm|{name:lambda *xs:False});cases+=1
    unknowns(lambda model:run('ekd7',values,model),mm,('ekcl','ekd3','ekd4','ekd6','ekdq'))
    assert run('ekea',values,m|{'zb7':lambda:c(3)});cases+=1
    changed=values[:];changed[pos['newfrequency']]=c(Q(1,4));assert not run('ekea',changed,m|{'zb7':lambda:c(3)});cases+=1
    names=('observer','frame','context','lengthunit','timeunit','oldobslower','oldobsupper','oldobsx','oldobsy','oldobsz')
    def move(*xs):return all(same_value(x,by[n],sortby[n],cuts) for x,n in zip(xs[:-1],names)) and r(xs[-1])==3
    for time in (-1,0,1,2,3):
        mm2=m|{'zb7':lambda:c(3),'eivu':move,'ekdc':lambda *xs:r(xs[-2])==Q(32,25) and same_value(xs[-1],by['oldoffset'],RS,cuts),'ekd5':lambda *xs:False}
        assert run('ekd6',values+[c(time)],mm2,'pointwise')==(time<0 or time>2);cases+=1
        assert run('ekd6',values+[c(time)],mm2|{'ekd5':lambda *xs:True},'pointwise');cases+=1
    return dict(cases=cases,all_59_roles_bound=True,source_and_receiver_periods_and_frames_not_swapped=True,new_interval_and_old_phase_rate_checked=True)

@lru_cache(None)
def universal_checks():
    cases=0
    for pivot,(name,sort) in enumerate(VARIABLES):
        for target in ('a','b','unavailable'):
            expected={n:'a' for n,t in SETTING};expected.update(frame='a',scope='b',context='case',light='a');expected[name]=target
            values=[expected[n] for i,(n,t) in enumerate(VARIABLES) if i!=pivot];row=tuple(expected[n] for n,t in SETTING)
            mm={'ra':lambda:'a','eisrx':lambda:'b','tc':lambda:'a','ekd7':lambda *xs,row=row:tuple(xs)==row,'ekea':lambda *xs:False};mode='slot:'+str(pivot)
            assert run('ekeb',values,mm,mode,('a','b'))==(target=='unavailable');cases+=1
            assert run('ekeb',values,mm|{'ekea':lambda *xs:True},mode,('a','b'));cases+=1
            assert run('ekeb',values,mm|{'ekd7':lambda *xs:False},mode,('a','b'));cases+=1
            if target!='unavailable':
                assert run('ekeb',values,mm|{'ekea':lambda *xs,row=row:tuple(xs)==row},mode,('a','b'));cases+=1
                assert not run('ekeb',values,mm|{'ekea':lambda *xs,row=row:tuple(xs)!=row},mode,('a','b'));cases+=1
    unknowns(lambda model:run('ekeb',values,model,mode,('a','b')),mm,('ekd7','ekea'))
    cuts,m=arithmetic();refused(lambda:run('ekeb',[],m|{'tc':lambda:cuts.make(5),'ekd7':lambda *xs:True,'ekea':lambda *xs:True}))
    return dict(cases=cases,quantified_slots=len(VARIABLES),same_assignment_conditional_not_existence_or_separate_witnesses=True,vacuous_cases_and_unknown_consequents_distinct=True)

@lru_cache(None)
def presentation_checks():
    rows={
      'eked':{'eisox':{('angular','ekec','case')},'zc':{('claim','author','ekec','ekeb','scope','case')},'ue':{('angular','claim','case'),('claim','dopplerdisplay','case')},'uf':{('author','claim','dopplerdisplay','case')}},
      'ekeg':{'eisox':{('dopplerdisplay','ekeb','case')}},
      'ekef':{'eir3':{('claim','author','paper','ekee','case')},'ue':{('parameters','claim','case')}},
      'ekei':{'eir3':{('dopplerdisplay','author','paper','ekeh','case')},'ue':{('claim','dopplerdisplay','case')}}}
    cases=0
    for root,rs in rows.items():cases+=perturb(lambda mm:run(root,[],mm),{n:relation(vs) for n,vs in rs.items()},rs)
    assert run('eked',[],{n:relation(vs) for n,vs in rows['eked'].items()}|{'ekec':forbidden,'ekeb':forbidden});cases+=1
    return dict(cases=cases,angular_equation_reference_consequence_and_colon_display_preserved=True,quotes_not_evaluated_as_physical_truth=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read('data/einstein-wave-cycle-frequency-reading-v1.json'));inv=json.loads(read(INVENTORY));segments=[]
    for i,row in enumerate(previous['units']):
        u=inv['units'][187+i];assert u['id']==row['unit'] and digest(u['text'].encode())==row['unit_sha256']
        segments.append(row|dict(range=[0,len(row['text'])],statements=[370+i],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',row['text']))))
    return dict(status='source_observer_phase_frequency_and_conditional_consequence_collated',segments=segments,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC,'data/einstein-wave-cycle-frequency-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==372 and new.document['statements'][:370]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in extract_document(new.document,roots=['ekd7'],statement_indices=[]).document['declarations']}
    assert {'ekcl','ekd3','ekd4','eivu','ekdm','ekdq','ekc7','ekdc','eissk','eissl'}<=names
    assert not names&{'ekdd','ekde','ekdt','ekds','ekdr','ekea','ekbw','ekbx','ekby','ekbz'}
    core=parse(read(CORE))
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=2,new_references=3,old_370_statements_and_judgments_preserved=True,doppler_conclusion_not_assumed_in_hypothesis=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('model',model_checks),('mapping',mapping_checks),('physical',physical_checks),('binding',binding_checks),('universal',universal_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_material_relative_frame','check_wave_inquiry','check_wave_transform_application','check_wave_cycle_frequency','check_distant_direction_geometry','check_resting_charge_force','check_velocity_angle_measure','compose_distant_direction_geometry','compose_wave_transform_application','compose_wave_cycle_frequency','compose_wave_display','compose_two_postulates','compose_field_equations','compose_material_relative_frame','compose_relativity_conjecture','compose_electromotive_wording','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*DEPENDENCIES,'scripts/compose_observed_doppler.py','scripts/check_observed_doppler.py','tests/test_observed_doppler.py',*(f'scripts/{n}.py' for n in helpers)}
    rows=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=s['statements'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']]
    return dict(status='physical_source_receiver_and_conditional_doppler_consequence_connected',document=FULL,**results,alignment=dict(segments=rows),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

