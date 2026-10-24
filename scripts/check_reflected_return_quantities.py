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
from scripts.check_mirror_wave_quantities import setting as previous_setting
from scripts.compose_reflected_return_quantities import *
from scripts.read_reflected_return_quantities import DOC,READING,INVENTORY,FACSIMILES,PRIOR,build_reading

CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','ri':'case','rd':'author','eirf':'paper','eisrx':'section7','eistk':'section8','eisuh':'incidentintro','eisuj':'reflectionintro','eisuk':'reflectiondisplay','eisuu':'returnintro','eisuv':'returndisplay'}|{symbol:field+'name' for rule,symbol,field,label in NAMES}
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'other','a','b']))
DEPENDENCIES=('reports/mirror-wave-quantities-v1.json','reports/reflected-light-inquiry-v1.json')
NAME_FIELDS={rule:field for rule,symbol,field,label in NAMES}
BOUNDS={'eks3':{'ekrz','ekhz','ekgf','ekc7'},'ektg':{'eks3'},'ekth':{'eks3','ektb'}}|{rule:{'eks3'} for rule in NAME_FIELDS}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','be','sjd','sky','soy','szi','shu','sedi'}|BOUNDS.get(name,set())
    if name in ('ektf','ekti','ektj','ektl','ektn'):bounds|=set(NAME_FIELDS)|{'ektg','ekth','ekso','ektk','ektm'}
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
            assert body['kind']==('exists' if isname or name=='ektg' else 'forall')
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
    c=cuts.make;_,by=previous_setting(cuts)
    by.update({n:c(x) for n,x in dict(labamplitude=Q(5,4),labanglecos=-1,labanglesin=0,labratio=0,labprincipal=0,labangle=Q(3,4),labperiod=3,labfrequency=Q(1,3)).items()})
    return [by[n] for n,t in SETTING],by

@lru_cache(None)
def binding_checks():
    cuts,m=arithmetic();c=cuts.make;values,by=setting(cuts);norm=normalize(cuts);cases=0
    rows={'ekrz':[norm([by[n] for n,t in PRIOR_SETTING])],
          'ekhz':[norm([False,*map(c,(0,Q(-3,4),-1,0,-1,Q(3,4))),by['labamplitude']])],
          'ekgf':[norm(list(map(c,(-1,0,0,1,0,0)))+[by[n] for n in ('labanglecos','labanglesin','labratio','labprincipal','pi','labangle')])],
          'ekc7':[norm([by[n] for n,t in HARMONIC]+[c(Q(1,2)),c(0),by['labperiod'],by['labfrequency']])]}
    mm=m|{n:lambda *xs,rows=rs:norm(xs) in rows for n,rs in rows.items()}
    assert run('eks3',values,mm);cases+=1
    for i,((n,t),(_,sort)) in enumerate(zip(SETTING,fixture('eks3')[1])):
        bad=values[:];bad[i]=c(4) if n=='speed' else c(Q(15,4)) if n=='light' else c(cuts.read(bad[i])+Q(1,7)) if t==R else True if t=='c' else sentinel(sort,100+i,cuts)
        assert not run('eks3',bad,mm),(i,n);cases+=1
    for n in rows:assert not run('eks3',values,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda model:run('eks3',values,model),mm,tuple(rows))
    assert len(SETTING)==90 and len(VARIABLES)==86 and all(len(name_witnesses(field))==84 for field in NAME_FIELDS.values());cases+=1
    return dict(cases=cases,all_90_roles_bound=True,same_inverse_wave_side_axis_and_period=True,printed_equations_not_premises=True)

@lru_cache(None)
def equation_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;_,by=setting(cuts);cases=0
    for speed in (-3,0,3):
        ratio=Q(speed,5);beta=Q(5,4) if speed else Q(1)
        for cosine in (-1,Q(1,3),Q(111,145),1):
            for refcos in (-1,Q(3775,7889),Q(2,3)):
                numerator=1-2*ratio*cosine+ratio*ratio
                # Deliberately independent input/output quantities expose all six
                # pairings even where the complete printed conjunction is false.
                row=by|{n:c(x) for n,x in dict(light=5,speed=speed,anglecos=cosine,refanglecos=refcos,amplitude=7,refamplitude=3,labamplitude=11,frequency=2,reffrequency=5,labfrequency=13,labanglecos=Q(1,7)).items()}
                mid=[3*beta*(1+ratio*refcos),(refcos+ratio)/(1+ratio*refcos),5*beta*(1+ratio*refcos)]
                right=[7*numerator/(1-ratio*ratio),-((1+ratio*ratio)*cosine-2*ratio)/numerator,2*numerator/(1-ratio)**2]
                expected=[(a,b) for lhs,x,y in zip((Q(11),Q(1,7),Q(13)),mid,right) for a,b in ((lhs,x),(x,y))];seen=[]
                def capture(a,b):seen.append((r(a),r(b)));return True
                assert run('ektb',[row[n] for n,t in SETTING],m|{'sca':capture});assert seen==expected,(seen,expected);cases+=6
                for name,args0,want in [('eks4',(5,speed,3,refcos),mid[0]),('eks5',(5,speed,cosine),numerator),('eks6',(5,speed,7,cosine),right[0]),('eks7',(5,speed,cosine),right[1]),('ekta',(5,speed,2,cosine),right[2])]:
                    assert r(run(name,list(map(c,args0)),m))==want;cases+=1
    # At zero speed all rows can hold simultaneously under a numerical angle
    # assignment. Altering each output is rejected by its own equality.
    row=by|{n:c(x) for n,x in dict(speed=0,anglecos=Q(3,5),refanglecos=Q(-3,5),labanglecos=Q(-3,5),amplitude=5,refamplitude=5,labamplitude=5,frequency=2,reffrequency=2,labfrequency=2).items()}
    assert run('ektb',[row[n] for n,t in SETTING],m);cases+=1
    for field in ('amplitude','refamplitude','labamplitude','frequency','reffrequency','labfrequency','refanglecos','labanglecos','anglecos'):
        bad=row|{field:c(r(row[field])+Q(1,7))};assert not run('ektb',[bad[n] for n,t in SETTING],m),field;cases+=1
    unknowns(lambda model:run('ektb',[row[n] for n,t in SETTING],model),m,('sca','sky','sjd','be'))
    return dict(cases=cases,all_three_rows_and_six_equalities_checked=True,frequency_denominator_not_corrected=True,outer_angle_minus_and_inverse_velocity_preserved=True)

@lru_cache(None)
def disagreement_checks():
    cuts,m=arithmetic();c,r=cuts.make,cuts.read;_,by=setting(cuts);cases=0
    normal=(Q(111,145),Q(48,145),Q(80,145));a,b,z=normal
    e1=(-b,1-b*b/(1+a),-b*z/(1+a));e2=(-z,-b*z/(1+a),1-z*z/(1+a));E=tuple(3*x+4*y for x,y in zip(e1,e2));H=(b*E[2]-z*E[1],z*E[0]-a*E[2],a*E[1]-b*E[0])
    returned_summary=[]
    for n,e,h,cosref in [((Q(1),Q(0),Q(0)),(Q(0),Q(3),Q(4)),(Q(0),Q(-4),Q(3)),Q(-1)),(normal,E,H,Q(3775,7889))]:
        ratio=Q(3,5);beta=Q(5,4);D=beta*(1-ratio*n[0]);nm=((n[0]-ratio)/(1-ratio*n[0]),n[1]/D,n[2]/D)
        en=(e[0],beta*(e[1]-ratio*h[2]),beta*(e[2]+ratio*h[1]));hn=(h[0],beta*(h[1]+ratio*e[2]),beta*(h[2]-ratio*e[1]))
        ret=list(map(c,(5,3,2*D,*nm,*en,*hn)));Krate=r(run('ekrk',ret,m));Knormal=run('ekrl',ret,m);ke=run('ekrm',ret,m);kh=run('ekrn',ret,m)
        factor=(1-2*ratio*n[0]+ratio*ratio)/(1-ratio*ratio)
        expected_n=((2*ratio-(1+ratio*ratio)*n[0])/(1-2*ratio*n[0]+ratio*ratio),n[1]/factor,n[2]/factor)
        assert Krate==2*factor and tuple(r(Knormal(x)) for x in ('x','y','z'))==expected_n;cases+=1
        coefs=[f(x) for f in (ke,kh) for x in ('x','y','z')]
        for side in (False,True):assert run('ekhz',[side,*coefs,c(5*factor)],m);cases+=1
        middle=r(run('eks4',list(map(c,(5,3,2*D,cosref))),m));printed=r(run('ekta',list(map(c,(5,3,2,n[0]))),m));derived=r(run('eks6',list(map(c,(5,3,2,n[0]))),m))
        assert derived==Krate and printed!=derived;cases+=1
        if n[0]==1:assert middle==Q(1,2) and printed==2;cases+=1
        else:assert middle!=derived;cases+=1
        returned_summary.append(dict(old_cosine=str(n[0]),physical_frequency=str(derived),middle_frequency=str(middle),rightmost_frequency=str(printed)))
    return dict(cases=cases,comparisons=returned_summary,normal_incidence_printed_disagreement=True,oblique_line_angle_disagreement_preserved=True,full_vector_and_both_polarization_sides_checked=True)

@lru_cache(None)
def quantifier_checks():
    cases=0
    for root in ['ektg','ekth',*NAME_FIELDS]:
        isname=root in NAME_FIELDS;fields=name_witnesses(NAME_FIELDS[root]) if isname else VARIABLES;universal=root=='ekth'
        for pivot,(variable,sort) in enumerate(fields):
            for target in ((False,True) if sort=='c' else ('a','b','unavailable')):
                assigned={n:False if t=='c' else ('a' if i%2==0 else 'b') for i,(n,t) in enumerate(SETTING)}|dict(frame='a',light='a',scope='b',context='case')
                if isname:assigned|={'wave':'a',NAME_FIELDS[root]:'b'}
                assigned[variable]=target;row=tuple(assigned[n] for n,t in SETTING);values=[assigned[n] for i,(n,t) in enumerate(fields) if i!=pivot]
                if isname:values=['a','b','case',*values]
                mm={'ra':lambda:'a','tc':lambda:'a','eisrx':lambda:'b','eks3':lambda *xs,row=row:xs==row};mode=f'slot:{pivot}'
                if universal:
                    assert run(root,values,mm|{'ektb':lambda *xs:False},mode,('a','b'))==(target=='unavailable');cases+=1
                    assert run(root,values,mm|{'ektb':lambda *xs,row=row:xs==row},mode,('a','b'));cases+=1
                else:
                    assert run(root,values,mm,mode,('a','b'))==(target!='unavailable');cases+=1
                    assert not run(root,values,mm|{'eks3':lambda *xs:False},mode,('a','b'));cases+=1
            unknowns(lambda model:run(root,values,model,mode,('a','b')),mm|{'ektb':lambda *xs:True},('eks3',))
        cuts,m=arithmetic();native=['wave',cuts.make(5),'case'] if isname else []
        refused(lambda:run(root,native,m|{'tc':lambda:cuts.make(5),'eks3':lambda *xs:True,'ektb':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_86_setting_and_84_naming_witness_slots_checked=True,boolean_side_and_infinite_domain_preserved=True,false_source_claim_not_executed_as_truth=True)

@lru_cache(None)
def presentation_checks():
    rows={'ekti':{'zc':{('returnintro','author','ektg','ekth','section8','case')},'eissb':{('returnintro','reflectiondisplay','author','ekso','ekth','section8','case')},'eisra':{('returnintro','author','paper','reflectionintro','ekso','ekth','section8','case')},'ue':{('incidentintro','reflectionintro','case'),('reflectionintro','returnintro','case'),('returnintro','returndisplay','case')},'uf':{('author','returnintro','returndisplay','case')}},
          'ektj':{'eislo':{(CONSTANTS[symbol],rule,'paper','case') for rule,symbol,field,label in NAMES},'eisox':{('returndisplay','ekth','case')}}};cases=0
    def final(node,author,series,scope,point):
        return (node,author,scope,point)==('returnintro','author','section8','case') and all(series(x)==(x in ('incidentintro','reflectionintro','returnintro')) for x in DOMAIN)
    for root,rs in rows.items():
        mm={n:relation(r) for n,r in rs.items()}|{'eisuz':final};cases+=perturb(lambda model:run(root,[],model),mm,rs)
        if root=='ekti':
            assert not run(root,[],mm|{'eisuz':lambda *xs:False});unknowns(lambda model:run(root,[],model),mm,('eisuz',));cases+=1
    # The generic final-stage relation preserves all arguments and distinguishes
    # the three selected introduction nodes from displays and other nodes.
    expected=('returnintro','author','section8','case')
    for slot in range(4):
        def wrong(node,author,series,scope,point,slot=slot):
            wanted=list(expected);wanted[slot]='other';return (node,author,scope,point)==tuple(wanted)
        mm={n:relation(r) for n,r in rows['ekti'].items()}|{'eisuz':wrong};assert not run('ekti',[],mm);cases+=1
    for changed in DOMAIN:
        def wrong_series(node,author,series,scope,point,changed=changed):
            return all(series(x)==((x in ('incidentintro','reflectionintro','returnintro')) != (x==changed)) for x in DOMAIN)
        mm={n:relation(r) for n,r in rows['ekti'].items()}|{'eisuz':wrong_series};assert not run('ekti',[],mm);cases+=1
    for root,msg,node,previous in [('ektl','ektk','returnintro','reflectiondisplay'),('ektn','ektm','returndisplay','returnintro')]:
        rs={'eir3':{(node,'author','paper',msg,'case')},'ue':{(previous,node,'case')}}
        cases+=perturb(lambda model:run(root,[],model),{n:relation(r) for n,r in rs.items()},rs)
    return dict(cases=cases,inverse_construction_reexpression_and_colon_bound=True,finally_scoped_to_same_three_stage_series=True,attribution_does_not_require_false_equalities=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==402 and new.document['statements'][:400]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[396,397,398,399])==selection_binding(old,[396,397,398,399])
    load_annotations(ROOT,BASIS,ANNOTATIONS);past=json.loads(read('data/mirror-wave-quantities-identifiers-v1.json'))['entries'];entries=json.loads(read(ANNOTATIONS))['entries'];assert entries[:len(past)]==past and len(entries)==len(past)+3
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,INDICES)['dependencies']);assert set(MEANINGS)|{'ekrz','ekrk','ekrl','ekrm','ekrn','ekgf','ekhz','ekc7','eisuz'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    reading=json.loads(read(READING));assert reading==build_reading();validate_hashes(ROOT,reading['source_sha256'])
    assert reading['reviewed_prose_characters']==80 and reading['reviewed_math_elements']==2
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,new_reference_individuals=len(PRIMITIVES)-1,all_400_previous_statements_and_meanings_preserved=True,all_three_rows_and_two_source_units_collated=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('binding',binding_checks),('equations',equation_checks),('disagreements',disagreement_checks),('quantifiers',quantifier_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_wave_transform_application','compose_reflected_light_inquiry','compose_mirror_wave_quantities','compose_wave_cycle_frequency','compose_doppler_infinity','check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_resting_charge_force','check_material_relative_frame','check_light_energy_ratio','check_wave_cycle_frequency','check_reflected_light_inquiry','check_mirror_wave_quantities','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_reflected_return_quantities.py','scripts/read_reflected_return_quantities.py','scripts/check_reflected_return_quantities.py','tests/test_reflected_return_quantities.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='reflected_K_return_and_all_printed_equalities_checked_with_disagreements_preserved',document=FULL,**results,alignment=dict(segments=json.loads(read(READING))['segments']),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
