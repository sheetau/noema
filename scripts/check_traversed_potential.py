"""Check signed work, potential units, full path binding and the printed relation."""
from functools import lru_cache
from copy import deepcopy
from fractions import Fraction as Q
from math import isqrt
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
# Load schema first: the historical checker chain is already deep.
from scripts.compose_traversed_potential import *
from scripts import check_electron_kinetic_work as prior
from scripts.check_clock_site_time import relation,perturb

DOC='docs/traversed-potential-v1.md';SOURCE='data/einstein-traversed-potential-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/direct-speed-experiment-v1.json','reports/electron-kinetic-work-v1.json','reports/kinetic-energy-consequences-v1.json','reports/potential-speed-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}|{'eis3w':'list','eis4c':'previous','eis3h':'energy_display'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),*[n for n,t in ALL if t=='a']]))
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;fn=prior.fn;sort=prior.sort;keyed=prior.keyed
BOUNDS={'er4':{'ek3u','ern'},'er6':{'seuw'},'er7':{'eou','er4','er6','seut'},'esb':{'er7'},'esc':{'esa'},'esd':{'esb','esc'},'ese':{'ep7','esb'},'esf':{'ep7','ese','esd'},'esh':{'er7'},'esi':{'esg'},'esj':{'esd','esh'},'esl':{'esk'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in prior.physical.NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='instance':
        d=next(d for d in doc['declarations'] if d['name']==root)
        def expose(x):
            if isinstance(x,list):return [expose(y) for y in x]
            if not isinstance(x,dict):return x
            if x.get('kind') in ('forall','exists'):
                d['parameters'].append(dict(name=x['variable'],sort=x['sort']));return expose(x['body'])
            return {k:expose(v) for k,v in x.items()}
        d['body']=expose(d['body'])
    return doc
@lru_cache(None)
def fixture(root,mode='native'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jtpslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtppoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtppoint',arguments=[]))
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='native'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jtppoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model():
    a=prior.model();c=a.c
    a.by.update(potential=a.register_function(prior.Rational((7,-2))),left=c(-1),right=c(1),drop=c(Q(1,8)),potentialunit='potentialunit',potentialscale=Q(1),chargescale=Q(1),chargerecord='chargerecord',speedunit='speedunit',speedscale=Q(1),speed=a.by['finalspeed'])
    for n,symbol in FIXED.items():
        if n in a.by:a.m[symbol]=lambda n=n:a.by[n]
    def square_root(x):
        z=a.r(x)
        if z<0:raise ValueError('Unknown negative square root')
        numerator,denominator=isqrt(z.numerator),isqrt(z.denominator)
        if numerator*numerator!=z.numerator or denominator*denominator!=z.denominator:raise ValueError('Unregistered irrational square root')
        return c(Q(numerator,denominator))
    a.m['cj']=square_root
    return a

@lru_cache(None)
def numeric_checks():
    a=model();c=a.c;cases=0
    for q in (Q(2),Q(-2),Q(3,2)):
        for speed,beta in ((0,1),(3,Q(5,4)),(4,Q(5,3))):
            drop=2*25*(beta-1)/q
            vals=list(map(c,(5,speed,2,q,drop)));assert run('esa',vals,a.m);cases+=1
            for j,value in ((2,3),(3,-q),(4,drop+1)):
                if speed==0 and j!=4:continue
                bad=vals.copy();bad[j]=c(value);assert not run('esa',bad,a.m);cases+=1
    # Keep the native seur validity checks, rather than mocking the equation itself.
    for vals in ((5,3,0,2,0),(5,-3,2,2,Q(25,4))):
        assert not run('esa',list(map(c,vals)),a.m);cases+=1
    reject(lambda:run('esa',list(map(c,(5,0,2,0,0))),a.m));cases+=1
    reject(lambda:run('esa',list(map(c,(5,3,2,2,Q(25,4)))),a.m|{'cj':forbidden}));cases+=1
    return dict(cases=cases,both_charge_signs_nonunit_mass_and_rest=True,printed_division_square_root_and_both_equalities=True,irrational_extension_not_silently_approximated=True)

@lru_cache(None)
def unit_checks():
    a=model();by=a.by;cases=0
    rows={'ek3u':[by[n] if n!='event' else by['end'] for n,t in energy.CHARGE],'ern':[by[n] for n,t in SPEED_UNITS],'eis4f':[by[n] for n in ('frame','energyunit','chargeunit','potentialunit','context')]}
    mm=a.m|keyed(a,rows);vals=a.values(SETTING);assert run('er4',vals,mm);cases+=1
    for n in rows:
        assert not run('er4',vals,mm|{n:lambda *xs:False});reject(lambda:run('er4',vals,mm|{n:forbidden}));cases+=2
    for n in ('matter','frame','end','chargeunit','charge','chargerecord','context','energyunit','potentialunit','speedunit'):
        bad=vals.copy();pos=[n for n,t in SETTING].index(n);bad[pos]=a.c(7) if n=='charge' else 'other' if n=='context' else 'a';assert not run('er4',bad,mm);cases+=1
    for pscale,qscale,wscale,wanted in ((2,3,6,True),(2,3,1,False),(-2,-3,6,False),(0,3,0,False)):
        b=by|dict(potentialscale=Q(pscale),chargescale=Q(qscale),energyscale=Q(wscale));r=rows|{'ek3u':[b[n] if n!='event' else b['end'] for n,t in energy.CHARGE]}
        assert run('er4',[b[n] for n,t in SETTING],a.m|keyed(a,r))==wanted;cases+=1
    return dict(cases=cases,physical_work_per_signed_charge_calibration=True,shared_charge_mass_length_time_energy_and_speed_units=True)

@lru_cache(None)
def path_checks():
    a=model();c=a.c;r=a.r;by=a.by;cases=0
    # Probe the actual whole-domain body at distinguishing interior points.
    vals=a.values(SETTING)
    for x,region,wanted in ((Q(0),True,True),(Q(1,2),False,False),(Q(2),False,True)):
        calls=[]
        def reg(*xs):calls.append(tuple(r(y) for y in xs));return region
        b=by|dict(region=fn(sort(REGION),reg));assert run('er5',[b[n] for n,t in SETTING]+[c(x)],a.m)==wanted;cases+=1
        if -1<=x<=1:assert calls==[(x,0,0,0)];cases+=1
    expected=by.copy()
    def potential(d,p,f,lo,hi,drop):
        # Boundary diagnostic only. The full potential definition is independently pinned.
        assert [d.implementation(c(t)) for t in (-2,-1,0,1,2)]==[False,True,True,True,False]
        return a.key((p,f,lo,hi,drop))==a.key((by['potential'],by['profile'],c(0),by['finalposition'],by['drop']))
    mm=a.m|{'seuw':potential}
    vs=vals+[c(Q(1,2)),c(Q(1,8))];assert run('er6',vs,mm,'instance');cases+=1
    assert not run('er6',vs,mm|{'seuw':lambda *xs:False},'instance');cases+=1
    bad=vs.copy();bad[[n for n,t in SETTING].index('region')]=fn(sort(REGION),lambda *xs:False);assert not run('er6',bad,mm,'instance');cases+=1
    # An interior detour beyond both endpoints is not hidden by the endpoint interval.
    bad=vs.copy();bad[[n for n,t in SETTING].index('curve')]=a.register_curve([prior.Rational((0,32,-128)),prior.Rational((0,)),prior.Rational((0,)),prior.Rational((0,1))]);assert not run('er6',bad,mm,'instance');cases+=1
    reject(lambda:run('er6',vals,mm));reject(lambda:run('er6',vs,mm|{'seuw':forbidden},'instance'));cases+=2
    return dict(cases=cases,whole_physical_interval_and_all_actual_path_positions=True,endpoint_only_and_outside_detour_rejected=True,unrestricted_real_quantification_refused=True)

@lru_cache(None)
def connection_checks():
    a=model();by=a.by;c=a.c;cases=0
    rows={'eou':a.values(energy.SETTING),'er4':a.values(SETTING),'er6':a.values(SETTING),'seut':[c(0),by['finalposition'],by['profile'],by['drop'],by['charge'],by['withdrawn']]}
    mm=a.m|keyed(a,rows);vals=a.values(ALL);assert run('er7',vals,mm);cases+=1
    for n in rows:
        assert not run('er7',vals,mm|{n:lambda *xs:False});reject(lambda:run('er7',vals,mm|{n:forbidden}));cases+=2
    # Every declared process/quantity/unit position is passed without a swap.
    for j,(n,t) in enumerate(ALL):
        bad=vals.copy();bad[j]='other' if t=='d' else 'a' if t=='a' else Q(9) if t=='b' else c(9) if t==R else a.register_function(prior.Rational((9,))) if t==F else by[n]
        if a.key([bad[j]])==a.key([vals[j]]):continue
        # initial/final/radiated are inherited balance parameters, deliberately unused by er7.
        if n in ('initial','final','radiated'):continue
        assert not run('er7',bad,mm),n;cases+=1
    assert run('esb',[],a.m|{'er7':keyed(a,{'er7':vals})['er7']});cases+=1
    assert run('esc',[],a.m|{'esa':keyed(a,{'esa':[by[n] for n,t in NUMERIC]})['esa']});cases+=1
    for root,parts in [('esd',('esb','esc')),('ese',('ep7','esb'))]:
        mm=a.m|{n:lambda:Content(('case','other'),(True,False)) for n in parts};assert run(root,[],mm);cases+=1
        for n in parts:assert not run(root,[],mm|{n:lambda:Content(('case','other'),(False,False))});cases+=1
    mm=a.m|{'er7':keyed(a,{'er7':vals})['er7']};assert run('esh',[by['matter'],by['drop'],'case'],mm);assert not run('esh',['a',by['drop'],'case'],mm);cases+=2
    def executable(x):
        if isinstance(x,dict):
            if x.get('kind')=='quote':return
            if x.get('kind')=='call':yield x['symbol']
            for y in x.values():yield from executable(y)
        elif isinstance(x,list):
            for y in x:yield from executable(y)
    # The literal massless intermediate expression remains preserved, but is not a premise.
    deps=extract_document(core(),roots=['ese'],statement_indices=[]).document
    assert not {'eo5','serg','eph'}&set(executable(deps));cases+=1
    return dict(cases=cases,same_electron_field_path_units_and_work=True,acquired_speed_and_final_energy_same_process=True,no_repair_or_use_of_massless_printed_intermediate=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislk':{('eis4q','list',Q(2),'paper','case')},'eiswm':{('eis4q','author','energy_display','ep7','paper','case')},'zc':{('eis4q','author','ese','esd','tenth','case')},'uh':{('eis4q','author','esd','tenth','case')},'uf':{('author','eis4q','eis4r','case')}}
    cases=perturb(lambda m:run('esf',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['esf']},rows)
    rows={'eisox':{('eis4r','esd','case')},'uh':{('eis4r','author','esd','tenth','case')},'eisnw':{('eis4r','author','eis4s','esh','paper','case')}}
    cases+=perturb(lambda m:run('esj',[],m),{n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in BOUNDS['esj']},rows)
    for root,node,msg,prev in [('esi','eis4q','esg','previous'),('esl','eis4r','esk','eis4q')]:
        rows={'eir3':{(node,'author','paper',msg,'case')},'ue':{(prev,node,'case')}}
        cases+=perturb(lambda m:run(root,[],m),{n:relation(rs) for n,rs in rows.items()}|{msg:forbidden},rows)
    return dict(cases=cases,second_item_energy_back_reference_inference_and_display=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    d=json.loads(read(INVENTORY));units=d['units'][268:270];math=[m for m in d['math'] if m['id'] in ('M0437','M0438')]
    for u in units:assert digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-traversed-potential-reading-v1',units=[dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=[m for m in math if m['id'] in u['math_ids']],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))) for u in units],facsimile_pages=[920,921],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==437 and after.document['statements'][:435]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[434])==selection_binding(before,[434]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES)+len(NEW_VALUES),new_statements=2,all_435_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('units',unit_checks),('path',path_checks),('connection',connection_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_traversed_potential.py','scripts/check_traversed_potential.py','tests/test_traversed_potential.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='traversed_potential_and_acquired_speed_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
