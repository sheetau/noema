"""Check actual curvature, exclusive normal action, and both literal formulas."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_local_magnetic_radius import *
from scripts import check_traversed_potential as base
from scripts import check_electron_deflection_response as physical
from scripts.check_clock_site_time import relation,perturb

DOC='docs/local-magnetic-radius-v1.md';SOURCE='data/einstein-local-magnetic-radius-reading-v1.json'
INVENTORY=base.INVENTORY;FACSIMILE=base.FACSIMILE
DEPENDENCIES=('reports/traversed-potential-v1.json','reports/magnetic-curvature-v1.json','reports/electron-deflection-response-v1.json','reports/electron-transformed-dynamics-v1.json','reports/magnetic-action-v1.json')
CONSTANTS=base.CONSTANTS|{n:n for n in REFERENCES}|{'eis3w':'list','eis4r':'previous','eisym':'equations'}
PEOPLE=tuple(dict.fromkeys([*physical.PEOPLE,*CONSTANTS.values(),*[n for n,t in SETTING if t=='a'],'otherforce','oppositeforce','radiusunit']))
forbidden=base.forbidden;reject=base.reject;walk=base.walk;fn=base.fn;sort=base.sort;keyed=physical.keyed
BOUNDS={'eso':{'ejsn','ek3n','ek3o','ek3u','ek3q','eibs','eico','esn'},'esp':{'eso','ejwb'},'est':{'esp'},'esu':{'esp'},'esv':{'esp'},'esw':{'esp'},'esx':{'ess'},'esy':{'est'},'esz':{'esu'},'es2':{'esv'},'es3':{'esy','esz','es2'},'es4':{'esp'},'es5':{'eso'},'eta':{'esn'},'es7':{'es6','es4','es5','esw','eta','esx','elk','esy','esz'},'etd':{'esz'},'etg':{'esy','esz','es2','es3'},'etj':{'es2'},'etc':{'etb'},'etf':{'ete'},'eti':{'eth'},'etl':{'etk'},'sepp':{'seob','senz','sjs','sepn'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in base.prior.physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode in ('instance','force_instance'):
        d=next(d for d in doc['declarations'] if d['name']==root)
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('forall','exists') and (mode=='instance' or x['sort']!='individual'):
                d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(v) for k,v in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jlmrslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jlmrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jlmrpoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jlmrpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(charge=2,N=5,ax=4):
    a=physical.model(3,charge,0,N);c=a.c;r=a.r
    ay=-Q(charge)*3*Q(N)/Q(25,2);X=Q(125,64)*ax*2/Q(charge)
    polys=[physical.Rational((0,3,Q(ax,2))),physical.Rational((0,0,ay/2)),physical.Rational((0,)),physical.Rational((0,1))]
    a.by.update(context='case',longitudinal=c(X),magnetic=c(N),radius=c(9/abs(ay)),radiusunit=a.by['lengthunit'],radiusscale=Q(1),curve=a.register_curve(polys),ax=c(ax),ay=c(ay),az=c(0),electricfield=a.field(lambda axis,p:X if axis=='x' else 0))
    a.by.update({n:a.register_function(p.derivative()) for (n,t),p in zip(response.PROFILES,polys)})
    for n,symbol in FIXED.items():a.m[symbol]=lambda n=n:a.by[n]
    # The cut reader is object-local; use an exact-square implementation here.
    from math import isqrt
    def square_root(x):
        z=r(x)
        if z<0:raise ValueError('Negative square root')
        n,d=isqrt(z.numerator),isqrt(z.denominator)
        if n*n!=z.numerator or d*d!=z.denominator:raise ValueError('Unregistered irrational root')
        return c(Q(n,d))
    a.m['cj']=square_root
    return a
def contribution(a,record,force):return [record,*[a.by[n] for n in ('matter','frame','event','forceunit')],force,a.by['context']]
def action_vectors(a):
    q=a.r(a.by['charge']);s=a.r(a.by['speed']);N=a.r(a.by['magnetic']);X=a.r(a.by['longitudinal']);V=a.r(a.by['light'])
    return a.point((X,0,0,0)),a.point((0,0,N,0)),a.point((s,0,0,0)),a.point((q*X,0,0,0)),a.point((0,-q*s*N/V,0,0))

@lru_cache(None)
def numeric_checks():
    cases=0
    for charge,N in ((2,5),(-2,-5),(3,2),(-3,-2)):
        a=model(charge,N);c=a.c;vs=a.values(NUMERIC)
        assert run('esq',vs,a.m);assert run('esr',vs,a.m);cases+=2
        for name in ('mass','charge','magnetic','radius'):
            bad=vs.copy();j=[n for n,t in NUMERIC].index(name);bad[j]=c(a.r(vs[j])+1)
            assert not run('esq',bad,a.m);assert not run('esr',bad,a.m);cases+=2
        # A correct positive radius does not repair the wrong acceleration direction.
        bad=vs.copy();j=[n for n,t in NUMERIC].index('ay');bad[j]=c(-a.r(vs[j]));assert not run('esq',bad,a.m);assert run('esr',bad,a.m);cases+=2
        bad=vs.copy();bad[3]=c(-charge);assert not run('esq',bad,a.m);assert not run('esr',bad,a.m);cases+=2
    a=model();vs=a.values(NUMERIC)
    for root in ('esq','esr'):
        reject(lambda:run(root,vs,a.m|{'cj':forbidden}));cases+=1
    for j in (3,4,6):
        bad=vs.copy();bad[j]=a.c(0);reject(lambda:run('esr' if j in (3,4) else 'esq',bad,a.m));cases+=1
    return dict(cases=cases,all_three_terms_and_literal_radius_expression=True,both_charge_and_field_signs_and_nonunit_mass=True,radius_alone_does_not_imply_acceleration_chain=True,zero_divisors_and_unknown_roots_refused=True)

@lru_cache(None)
def exclusive_checks():
    a=model();by=a.by;c=a.c;cases=0
    E,B,V,EF,MF=action_vectors(a)
    actual=[contribution(a,by['electricrecord'],EF),contribution(a,by['magneticrecord'],MF)]
    magnetic=tuple(by[n] for n in ('magneticrecord','matter','frame','event','context'))
    def mm(rows):return a.m|{'eis4t':lambda *xs:a.key(xs) in {a.key(row) for row in rows},'eirt':lambda *xs:xs==magnetic}
    for vector,wanted in (((7,0,0,0),True),((0,1,0,0),False),((0,0,1,0),False),((0,0,0,0),True)):
        force=a.point(vector);rows=actual+[contribution(a,'otherforce',force)];m=mm(rows)
        assert run('esm',a.values(SETTING)+['otherforce',force],m)==wanted;cases+=1
        assert run('esn',a.values(SETTING)+['otherforce',force],m,'instance')==wanted;cases+=1
        # Keep the record quantifier native: a hidden record cannot escape the condition.
        assert run('esn',a.values(SETTING)+[force],m,'force_instance')==wanted;cases+=1
    left=a.point((0,1,0,0));right=a.point((0,-1,0,0));rows=actual+[contribution(a,'otherforce',left),contribution(a,'oppositeforce',right)]
    for record,force in [('otherforce',left),('oppositeforce',right)]:assert not run('esn',a.values(SETTING)+[record,force],mm(rows),'instance');cases+=1
    assert run('esm',a.values(SETTING)+[by['magneticrecord'],MF],mm(actual));cases+=1
    assert not run('esn',a.values(SETTING)+['otherforce',left],mm([]),'instance');cases+=1
    reject(lambda:run('esn',a.values(SETTING),mm(actual)));reject(lambda:run('esm',a.values(SETTING)+['otherforce',left],mm(actual)|{'eis4t':forbidden}));cases+=2
    return dict(cases=cases,all_actual_contributions_not_just_observed_records=True,nonmagnetic_tangential_actions_allowed=True,cancelling_normal_actions_still_rejected=True,record_quantifier_native_and_function_quantifier_refused=True)

def physical_rows(a):
    by=a.by;c=a.c;E,B,V,EF,MF=action_vectors(a)
    vals=by|dict(point=by['location'],carrier=by['matter'],electricconversion=c(1),magneticconversion=c(Q(1,5)))
    ea=vals|dict(forcerecord=by['electricrecord'],fieldunit=by['electricunit'],electric=E,force=EF,conversion=c(1))
    ma=vals|dict(forcerecord=by['magneticrecord'],magnetic=B,velocity=V,force=MF,conversion=c(Q(1,5)))
    rows={name:[vals[n] for n,t in fields] for name,fields in [('ejsn',response.FIELDS),('ek3n',response.UNITS),('ek3o',response.MASS),('ek3u',response.CHARGE),('ek3q',response.KINEMATIC)]}
    rows|={'eibs':[ea[n] for n,t in response.ELECTRIC],'eico':[ma[n] for n,t in response.MAGNETIC],'esn':a.values(SETTING),'eisqd':[by[n] for n in ('matter','frame','event','lengthunit','timeunit','location','context')]}
    return rows
@lru_cache(None)
def physical_checks():
    cases=0
    for charge,N in ((2,5),(-2,-5)):
        a=model(charge,N);by=a.by;c=a.c;rows=physical_rows(a);mm=a.m|keyed(a,rows);vs=a.values(SETTING)
        assert run('eso',vs,mm);cases+=1
        for n in rows:
            assert not run('eso',vs,mm|{n:lambda *xs:False});reject(lambda:run('eso',vs,mm|{n:forbidden}));cases+=2
        for n,t in SETTING:
            if t not in ('a','b','d') or n in ('radiusunit','radiusscale'):continue
            j=[n for n,t in SETTING].index(n);bad=vs.copy();bad[j]='other' if t=='d' else 'a' if t=='a' else Q(9);assert not run('eso',bad,mm),n;cases+=1
        for field in ('electricfield','magneticfield'):
            old=by[field]
            for axis in ('x','y','z'):
                bad=vs.copy();bad[[n for n,t in SETTING].index(field)]=a.field(lambda ax,p:a.r(old(ax)(*map(c,p)))+(ax==axis))
                assert not run('eso',bad,mm|{'ejsn':lambda *xs:True,'eibs':lambda *xs:True,'eico':lambda *xs:True,'esn':lambda *xs:True});cases+=1
    # Execute real derivative composition independently from role-boundary tests.
    from scripts.compose_material_acceleration import AT
    a=model();values=a.by|dict(point=a.by['location']);vs=[values[n] for n,t in AT]
    assert run('sepp',vs,a.m);cases+=1
    for n,t in response.ACCEL:
        bad=vs.copy();bad[[x for x,t in AT].index(n)]=a.c(a.r(values[n])+1);assert not run('sepp',bad,a.m);cases+=1
    assert 'setk' not in {d['name'] for d in boundary('eso')['declarations']};cases+=1
    return dict(cases=cases,same_electron_event_actual_trajectory_and_calibrated_fields=True,both_physical_force_contributions_and_exclusion=True,actual_second_derivatives_separately_evaluated=True,second_equation_not_hidden_in_physical_setting=True)

@lru_cache(None)
def geometry_checks():
    cases=0
    for tangential in (0,4,100,-7):
        a=model(ax=tangential);by=a.by;c=a.c;mm=a.m|{'eso':lambda *xs:True,'ejwb':lambda *xs:xs==(by['radiusunit'],Q(1),Q(0),Q(0),Q(1),'case')};vs=a.values(SETTING)
        assert run('esp',vs,mm);cases+=1
        for n,value in [('radius',-a.r(by['radius'])),('radius',a.r(by['radius'])+1),('ay',0),('az',1)]:
            bad=vs.copy();bad[[x for x,t in SETTING].index(n)]=c(value);assert not run('esp',bad,mm);cases+=1
        bad=vs.copy();bad[[n for n,t in SETTING].index('radiusscale')]=Q(2);assert not run('esp',bad,mm|{'ejwb':lambda *xs:True});cases+=1
        assert not run('esp',vs,mm|{'eso':lambda *xs:False});cases+=1
    a=model();vs=a.values(SETTING);mm=a.m|{'esp':lambda *xs:True}
    assert run('ess',vs,a.m);assert run('est',vs,mm);assert run('esu',vs,mm);assert run('esv',vs,mm);cases+=4
    bad=vs.copy();bad[[n for n,t in SETTING].index('ay')]=a.c(-a.r(a.by['ay']))
    assert not run('est',bad,mm);assert not run('esu',bad,mm);assert run('esv',bad,mm);cases+=3
    return dict(cases=cases,curvature_from_same_three_velocity_and_acceleration_values=True,tangential_acceleration_does_not_change_radius=True,positive_radius_and_length_scale_preserved=True,second_equation_required_for_reformulation=True)

@lru_cache(None)
def connection_checks():
    a=model();cases=0;vs=a.values(SETTING)
    for root,target in [('esw','esp'),('esx','ess'),('esy','est'),('esz','esu'),('es2','esv'),('eta','esn')]:
        mm=a.m|keyed(a,{target:vs});assert run(root,[],mm);assert not run(root,[],mm|{target:lambda *xs:False});cases+=2
    for root,value,target in [('es4','radius','esp'),('es5','magnetic','eso')]:
        mm=a.m|keyed(a,{target:vs});args=[a.by['matter'],a.by[value],'case'];assert run(root,args,mm);cases+=1
        bad=args.copy();bad[1]=a.c(a.r(a.by[value])+1);assert not run(root,bad,mm);cases+=1
        bad=args.copy();bad[0]='a';assert not run(root,bad,mm);cases+=1
    for premise in (False,True):
        for left in (False,True):
            for right in (False,True):
                mm=a.m|{n:lambda x=x:Content(('case','other'),(x,False)) for n,x in [('esy',premise),('esz',left),('es2',right)]}
                assert run('es3',[],mm)==(not premise or left==right);cases+=1
    q=next(d for d in core()['declarations'] if d['name']=='es6');assert {x.get('symbol') for x in walk(q['body']) if x.get('kind')=='call'}=={'es4','eisxh','ri'};cases+=1
    return dict(cases=cases,current_magnetic_case_separate_from_electrostatic_history=True,radius_question_does_not_embed_the_answer_formula=True,conditional_equivalence_truth_table_not_exclusive_or=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislk':{('eis4u','list',Q(3),'paper','case')},'eiszy':{('eis4u','author','es6','tenth','case')},'eisnw':{('eis4u','author','eis4y','es4','paper','case'),('eis4u','author','eis4z','es5','paper','case')},'ug':{('eis4u','author','esw','tenth','case')},'eisa5':{('eis4u','author','esw','eta','case')},'eis3v':{('esx','elk',Q(2),'case')},'eiswm':{('eis4u','author','equations','elk','paper','case')},'zc':{('eis4u','author','esy','esz','tenth','case')},'uf':{('author','eis4u','eis4v','case')}}
    cases=perturb(lambda m:run('es7',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['es7']},rows)
    for root,node,target in [('etd','eis4v','esz'),('etj','eis4x','es2')]:
        rows={'eisox':{(node,target,'case')},'uh':{(node,'author',target,'tenth','case')}};cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS[root]},rows)
    rows={'zd3':{('eis4w','author','esy','esz','es2','tenth','case')},'uh':{('eis4w','author','es3','tenth','case')},'uf':{('author','eis4w','eis4x','case')}}
    cases+=perturb(lambda m:run('etg',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['etg']},rows)
    for root,node,msg,prev in [('etc','eis4u','etb','previous'),('etf','eis4v','ete','eis4u'),('eti','eis4w','eth','eis4v'),('etl','eis4x','etk','eis4w')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(prev,node,'case')}};cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{msg:forbidden},rows)
    return dict(cases=cases,third_item_question_condition_and_parenthetical_exclusion=True,second_A_back_reference_reason_and_both_displays=True,oder_as_same_premise_reformulation=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][270:274];math=[m for m in d['math'] if m['id'] in ('M0439','M0440','M0441','M0442')]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-local-magnetic-radius-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[m for m in math if m['id'] in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))) for u in units],facsimile_pages=[921],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==441 and after.document['statements'][:437]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[435,436])==selection_binding(before,[435,436]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES)+len(NEW_VALUES),new_statements=4,all_437_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('exclusive',exclusive_checks),('physical',physical_checks),('geometry',geometry_checks),('connection',connection_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_local_magnetic_radius.py','scripts/check_local_magnetic_radius.py','tests/test_local_magnetic_radius.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='sole_magnetic_deflection_and_local_radius_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
