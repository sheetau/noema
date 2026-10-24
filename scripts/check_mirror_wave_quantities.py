"""Check shared quantity roles, literal printed equations and inherited angle disagreement."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_conductor_cases import sentinel
from scripts.check_resting_charge_force import retag
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_light_energy_ratio import arithmetic
from scripts.check_wave_cycle_frequency import refused
from scripts.check_reflected_light_inquiry import normalize,settings as prior_settings
from scripts.compose_mirror_wave_quantities import *
from scripts.read_mirror_wave_quantities import DOC,READING,INVENTORY,FACSIMILES,PRIOR,build_reading

CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','ri':'case','rd':'author','eirf':'paper','eisrx':'section7','eistk':'section8','eisue':'mirror','eisug':'query','eisuh':'incidentintro','eisui':'incidentdisplay','eisuj':'reflectionintro','eisuk':'reflectiondisplay'}|{symbol:field+'name' for rule,symbol,field,label in NAMES}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'other','a','b']))
DEPENDENCIES=('reports/reflected-light-inquiry-v1.json','reports/perfect-mirror-setting-v1.json','reports/aberration-line-v1.json','reports/aberration-presentation-v1.json','reports/observed-amplitude-v1.json','reports/wave-cycle-frequency-v1.json')
NAME_FIELDS={rule:field for rule,symbol,field,label in NAMES}
BOUNDS={'ekrz':{'ekrf','ekgn','ekhz','ekgf','ekc7','ekgc'},'eksm':{'ekrz'},'eksn':{'ekrz','ekr3'},'ekso':{'ekrz','ekr4'}}|{rule:{'ekrz'} for rule in NAME_FIELDS}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('eksj','eksk','eksl','eksp','eksq','eksr','ekss','eksu','eksw','eksy','eks2'):bounds|=set(NAME_FIELDS)|{'ekrg','eksm','eksn','ekso','ekst','eksv','eksx','eksz'}
    abstract(doc,bounds);return extract_document(doc,roots=[name],statement_indices=[]).document

@lru_cache(None)
def fixture(name,mode='native'):
    doc=deepcopy(boundary(name))
    if mode.startswith('slot:'):
        doc=retag(doc)
        for d in doc['declarations']:
            if d['kind']=='primitive':
                d['parameters']=['individual' if isinstance(s,dict) and s.get('kind')=='function' else s for s in d['parameters']]
                if isinstance(d['result'],dict) and d['result'].get('kind')=='function':d['result']='individual'
            else:
                for p in d['parameters']:
                    if isinstance(p['sort'],dict) and p['sort'].get('kind')=='function':p['sort']='individual'
        d=next(d for d in doc['declarations'] if d['name']==name);isname=name in NAME_FIELDS;body=d['body'] if isname else d['body']['body'];fields=name_witnesses(NAME_FIELDS[name]) if isname else VARIABLES;pivot=int(mode.split(':')[1]);retained=None
        for i,(n,t) in enumerate(fields):
            assert body['kind']==('exists' if isname or name=='eksm' else 'forall')
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        if isname:d['body']=retained|{'body':body}
        else:d['body']['body']=retained|{'body':body}
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmwq'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        if not any(x['name']=='ri' for x in doc['declarations']):doc['declarations'].append(dict(kind='primitive',name='ri',parameters=[],result='situation'))
        expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='ri',arguments=[]))
    elif isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jmwqcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jmwqcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots),(name,len(values),len(slots));captured=[]
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    def capture(x):captured.append(x);return True
    mm['jmwqcapture']=capture
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def setting(cuts):
    c=cuts.make;_,by=prior_settings(cuts)
    by.update(magneticside=False)
    by.update({n:c(x) for n,x in dict(amplitude=5,newamplitude=Q(5,2),refamplitude=Q(5,2),newanglecos=1,newanglesin=0,newratio=0,newprincipal=0,newangle=0,refanglecos=-1,refanglesin=0,refratio=0,refprincipal=0,refangle=Q(3,4),refperiod=Q(3,2),reffrequency=Q(2,3)).items()})
    return [by[n] for n,t in SETTING],by

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c=cuts.make;values,by=setting(cuts);norm=normalize(cuts);cases=0
    old=[by[n] for n in ('ex','ey','ez','hx','hy','hz')];new=list(map(c,(0,Q(3,2),2,0,-2,Q(3,2))));ref=list(map(c,(0,Q(-3,2),-2,0,-2,Q(3,2))))
    rows={'ekrf':[norm([by[n] for n,t in MIRROR])],'ekgn':[norm([by[n] for n,t in LINE_SETTING])],'ekhz':[norm([False,*a,by[n]]) for a,n in [(old,'amplitude'),(new,'newamplitude'),(ref,'refamplitude')]],'ekgf':[norm(list(map(c,(-1,0,0,1,0,0)))+[by[n] for n in ('refanglecos','refanglesin','refratio','refprincipal','pi','refangle')])],'ekc7':[norm([by[n] for n,t in HARMONIC]+[c(1),c(0),by['refperiod'],by['reffrequency']])]}
    geom=norm([by[n] for n,t in GEOMETRY])
    def line(*xs):
        good=norm(xs)==geom;return FunctionValue(('individual',),RS,lambda a:c(1 if a==('x' if good else 'y') else 0))
    mm=m|{'ekgc':line}|{n:lambda *xs,rows=rs:norm(xs) in rows for n,rs in rows.items()}
    assert run('ekrz',values,mm);cases+=1
    for i,((n,t),(_,sort)) in enumerate(zip(SETTING,fixture('ekrz')[1])):
        bad=values[:];bad[i]=c(4) if n=='speed' else c(Q(15,4)) if n=='light' else c(cuts.read(bad[i])+Q(1,7)) if t==R else True if t=='c' else sentinel(sort,100+i,cuts)
        assert not run('ekrz',bad,mm),(i,n);cases+=1
    for n in rows:assert not run('ekrz',values,mm|{n:lambda *xs:False});cases+=1
    for row in rows['ekhz']:
        remain=[r for r in rows['ekhz'] if r!=row];assert not run('ekrz',values,mm|{'ekhz':lambda *xs:norm(xs) in remain});cases+=1
    unknowns(lambda model:run('ekrz',values,model),mm,(*rows,'ekgc'))
    assert len(values)==82 and len(VARIABLES)==78 and all(len(name_witnesses(field))==76 for field in NAME_FIELDS.values());cases+=1
    return dict(cases=cases,all_82_roles_and_same_boolean_side_shared=True,three_magnitudes_same_line_reflected_normal_and_cycle_bound=True,printed_equations_not_in_premise=True)

@lru_cache(None)
def equation_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=setting(cuts);cases=0
    for speed in (-3,0,3):
        beta=Q(5,4) if speed else Q(1)
        for cosine in (-1,Q(1,3),Q(111,145),1):
            for amplitude,frequency in ((3,2),(5,7)):
                D=beta*(1-Q(speed,5)*cosine);moving=(cosine-Q(speed,5))/(1-Q(speed,5)*cosine)
                row=by|{n:c(x) for n,x in dict(light=5,speed=speed,anglecos=cosine,amplitude=amplitude,newamplitude=amplitude*D,newanglecos=moving,frequency=frequency,newfrequency=frequency*D,refamplitude=amplitude*D,refanglecos=-moving,reffrequency=frequency*D).items()}
                args=[row[n] for n,t in SETTING];assert run('ekr3',args,m) and run('ekr4',args,m);cases+=2
                for name,fields in [('ekr3',('newamplitude','newanglecos','newfrequency')),('ekr4',('refamplitude','refanglecos','reffrequency'))]:
                    for field in fields:
                        bad=row|{field:c(r(row[field])+Q(1,7))};assert not run(name,[bad[n] for n,t in SETTING],m);cases+=1
    unknowns(lambda model:run('ekr3',args,model),m,('sca','sky','sjd'))
    unknowns(lambda model:run('ekr4',args,model),m,('sca','be'))
    return dict(cases=cases,all_six_printed_equalities_distinguished=True,amplitude_not_square_and_frequency_not_phase_rate=True,native_formulas_do_not_assert_their_physical_truth=True)

@lru_cache(None)
def literal_angle_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;values,by=setting(cuts);cases=0
    n=(Q(111,145),Q(48,145),Q(80,145));g=list(map(c,(5,3,*n)))
    moving=run('ekgd',g,m);line=run('ekgc',g,m);nm=tuple(r(moving(a)) for a in ('x','y','z'));nl=tuple(r(line(a)) for a in ('x','y','z'))
    assert nm==(Q(15,49),Q(24,49),Q(40,49)) and nl==(Q(111,161),Q(60,161),Q(100,161));cases+=1
    current=sum(a*b for a,b in zip(nm,nl));reflected=sum(a*b for a,b in zip((-nm[0],*nm[1:]),nl))
    assert current==Q(145,161)!=nm[0] and reflected==Q(3775,7889)!=-current and nm[0]>0;cases+=1
    a,b,z=n;e1=(-b,1-b*b/(1+a),-b*z/(1+a));e2=(-z,-b*z/(1+a),1-z*z/(1+a));E=tuple(3*x+4*y for x,y in zip(e1,e2));H=(b*E[2]-z*E[1],z*E[0]-a*E[2],a*E[1]-b*E[0])
    assert sum(x*x for x in E)==sum(x*x for x in H)==25 and sum(x*y for x,y in zip(n,E))==0;cases+=1
    beta=Q(5,4);ratio=Q(3,5);En=(E[0],beta*(E[1]-ratio*H[2]),beta*(E[2]+ratio*H[1]));Hn=(H[0],beta*(H[1]+ratio*E[2]),beta*(H[2]-ratio*E[1]));D=Q(98,145)
    reflected_fields=(En[0],-En[1],-En[2],-Hn[0],Hn[1],Hn[2])
    for side in (False,True):
        for amps,A in [((*E,*H),Q(5)),((*En,*Hn),5*D),(reflected_fields,5*D)]:assert run('ekhz',[side,*map(c,amps),c(A)],m);cases+=1
    by.update({n:c(x) for n,x in dict(light=5,speed=3,anglecos=n[0],amplitude=5,newamplitude=5*D,refamplitude=5*D,frequency=2,newfrequency=2*D,reffrequency=2*D,newanglecos=current,refanglecos=reflected).items()})
    args=[by[n] for n,t in SETTING];assert not run('ekr3',args,m) and not run('ekr4',args,m);cases+=2
    # The scalar amplitude and frequency equations agree; replacing only each
    # printed angle value makes its conjunction true, identifying the mismatch.
    by['newanglecos']=c(nm[0]);assert run('ekr3',[by[n] for n,t in SETTING],m);cases+=1
    by['newanglecos']=c(current);by['refanglecos']=c(-current);assert run('ekr4',[by[n] for n,t in SETTING],m);cases+=1
    return dict(cases=cases,old_normal=[str(x) for x in n],moving_normal=[str(x) for x in nm],moving_line=[str(x) for x in nl],actual_moving_cosine=str(current),printed_moving_cosine=str(nm[0]),actual_reflected_cosine=str(reflected),printed_reflected_cosine=str(-current),inherited_line_angle_not_silently_changed_to_axis=True,nonzero_transverse_wave_and_mirror_incidence_preserved=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for root in ['eksm','eksn','ekso',*NAME_FIELDS]:
        isname=root in NAME_FIELDS;fields=name_witnesses(NAME_FIELDS[root]) if isname else VARIABLES;universal=root in ('eksn','ekso');result='ekr3' if root=='eksn' else 'ekr4'
        for pivot,(variable,sort) in enumerate(fields):
            for target in ((False,True) if sort=='c' else ('a','b','unavailable')):
                assigned={n:False if t=='c' else ('a' if i%2==0 else 'b') for i,(n,t) in enumerate(SETTING)}|dict(frame='a',light='a',scope='b',context='case')
                if isname:assigned|={'wave':'a',NAME_FIELDS[root]:'b'}
                assigned[variable]=target;row=tuple(assigned[n] for n,t in SETTING);values=[assigned[n] for i,(n,t) in enumerate(fields) if i!=pivot]
                if isname:values=['a','b','case',*values]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','ekrz':lambda *xs,row=row:xs==row}
                mode=f'slot:{pivot}'
                if universal:
                    assert run(root,values,mm|{result:lambda *xs:False},mode,('a','b'))==(target=='unavailable');cases+=1
                    assert run(root,values,mm|{result:lambda *xs,row=row:xs==row},mode,('a','b'));cases+=1
                else:
                    assert run(root,values,mm,mode,('a','b'))==(target!='unavailable');cases+=1
                    assert not run(root,values,mm|{'ekrz':lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(root,values,model,mode,('a','b')),mm|{result:lambda *xs:True},('ekrz',))
        cuts,m=arithmetic();native=['wave',cuts.make(5),'case'] if isname else []
        refused(lambda:run(root,native,m|{'tc':lambda:cuts.make(5),'ekrz':lambda *xs:True,result:lambda *xs:True}));cases+=1
    return dict(cases=cases,all_78_setting_quantifiers_and_76_witnesses_per_name_bound=True,boolean_side_is_not_retagged_to_an_individual=True,display_implications_can_be_false_without_changing_premise=True,native_infinite_domains_refused=True)

@lru_cache(None)
def presentation_checks():
    old={'eislo':{(CONSTANTS[NAMES[i][1]],NAMES[i][0],'paper','case') for i in (0,3,6)}}
    new={'eislo':{(CONSTANTS[NAMES[i][1]],NAMES[i][0],'paper','case') for i in (1,4,7)}}
    ref={'eislo':{(CONSTANTS[NAMES[i][1]],NAMES[i][0],'paper','case') for i in (2,5,8)}}
    rows={
      'eksp':old|{'eislz':{('incidentintro','author','eksm','section8','case')},'ug':{('incidentintro','author','eksm','section8','case')},'eissb':{('incidentintro','mirror','author','ekrg','eksm','section8','case')},'uh':{('incidentintro','author','eksn','section8','case')},'uf':{('author','incidentintro','incidentdisplay','case')},'ue':{('incidentintro','incidentdisplay','case')}},
      'eksq':new|{'eisox':{('incidentdisplay','eksn','case')}},
      'eksr':{'zc':{('reflectionintro','author','eksm','ekso','section8','case')},'eisra':{('reflectionintro','author','paper','incidentintro','eksm','ekso','section8','case')},'uf':{('author','reflectionintro','reflectiondisplay','case')},'ue':{('reflectionintro','reflectiondisplay','case')}},
      'ekss':ref|{'eisox':{('reflectiondisplay','ekso','case')}},
    };cases=0
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(r) for n,r in rs.items()},rs)
    for root,msg,node,previous in [('eksu','ekst','incidentintro','query'),('eksw','eksv','incidentdisplay','incidentintro'),('eksy','eksx','reflectionintro','incidentdisplay'),('eks2','eksz','reflectiondisplay','reflectionintro')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(previous,node,'case')}}
        cases+=perturb(lambda model:run(root,[],model),{n:relation(r) for n,r in rows.items()},rows)
    return dict(cases=cases,parameter_specification_frame_condition_and_both_colons_preserved=True,nine_quantity_names_keep_same_setting=True,attributed_false_angle_claim_not_executed_as_truth=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==400 and new.document['statements'][:396]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[394,395])==selection_binding(old,[394,395])
    load_annotations(ROOT,BASIS,ANNOTATIONS);past=json.loads(read('data/reflected-light-inquiry-identifiers-v1.json'))['entries'];entries=json.loads(read(ANNOTATIONS))['entries'];assert entries[:len(past)]==past and len(entries)==len(past)+9
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'ekrf','ekgn','ekgc','ekgf','ekhz','ekc7','eislo','eisox'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['reviewed_prose_characters']==184 and reading['reviewed_math_elements']==6
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_reference_individuals=len(PRIMITIVES),all_396_previous_statements_and_meanings_preserved=True,all_six_math_elements_and_six_display_rows_collated=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binding',binding_checks),('equations',equation_checks),('literal_angle',literal_angle_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_wave_transform_application','compose_aberration_line','compose_perfect_mirror_setting','compose_wave_cycle_frequency','compose_doppler_infinity','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_reflected_light_inquiry','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_mirror_wave_quantities.py','scripts/read_mirror_wave_quantities.py','scripts/check_mirror_wave_quantities.py','tests/test_mirror_wave_quantities.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='incident_and_reflected_k_quantities_and_literal_angle_disagreement_checked',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
