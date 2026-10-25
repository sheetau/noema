"""Check operational maps, quantified scope, caution and quoted inference."""
from functools import lru_cache
from copy import deepcopy
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document,FunctionValue,Content
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_alternative_conventions as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_convention_caution import *

DOC='docs/electron-convention-caution-v1.md';SOURCE='data/einstein-electron-convention-caution-reading-v1.json'
INVENTORY=prior.INVENTORY;FACSIMILE=prior.FACSIMILE
DEPENDENCIES=('reports/electron-alternative-conventions-v1.json','reports/electron-directional-masses-v1.json')
CONSTANTS=prior.CONSTANTS|{n:n for n in REFERENCES}|{'zrcsubject':'topic','zrcrole':'role'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'a','b']))
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk;NUM=prior.NUM
BOUNDS={'enz':{'enk'},'enu':{'ens'},'env':{'emf','ent','enu'},'enw':{'env'},'en2':{'vd'},'en3':{'en2'},'en4':{'en3','seqm'},'en5':{'en4'},'en6':{'en3','en5'},'en7':{'enw','en6','enb'},'eob':{'eoa'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in NUM|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document
@lru_cache(None)
def fixture(root):
    doc=deepcopy(boundary(root));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jeccslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jeccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jeccpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jecccapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jecccapture',arguments=[expr])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,m,small=False):
    doc,slots=fixture(root);assert len(values)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=('a' if small else x):x for n,x in CONSTANTS.items()}|{'jeccpoint':lambda:'case','jecccapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    result=evaluate_document(doc,individuals=('a','b') if small else PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def mapvalue(a,factors):
    pointsort=next(d for d in core()['declarations'] if d['name']=='enx')['result']
    return FunctionValue((pointsort,),pointsort,lambda p:a.point([factor*a.r(p(axis)) for factor,axis in zip(factors,('x','y','z'))]+[0]))

@lru_cache(None)
def numerical_checks():
    cases=0
    for speed in (0,3):
        a=prior.model(speed);c,r=a.c,a.r;mu=r(a.by['mass']);L=mu*a.beta**3;T=mu*a.beta**2
        identity=mapvalue(a,(1,1,1));changed=mapvalue(a,(a.beta**3,a.beta**2,a.beta**2))
        assert tuple(r(run('enp',a.values(CONVENTION),a.m)(x)) for x in ('x','y','z'))==tuple(r(a.by['force'](x)) for x in ('x','y','z'));cases+=1
        acceleration=run('enq',a.values(CONVENTION),a.m)
        assert tuple(r(acceleration(x)) for x in ('x','y','z'))==tuple(r(a.by[n]) for n,t in ACCEL);cases+=1
        assert run('enz',a.values(CONVENTION),a.m|{'enk':lambda *xs:a.key(xs)==a.key(a.values(CONVENTION))});cases+=1
        for name in ('newax','neway','newaz'):
            values=a.values(CONVENTION);i=[n for n,t in CONVENTION].index(name);values[i]=c(r(values[i])+1)
            assert not run('enz',values,a.m|{'enk':lambda *xs:True});cases+=1
        for inputs in ((0,0,0),(1,0,0),(0,1,0),(0,0,1),(2,-3,5)):
            vector=a.point([*inputs,0]);mapped=run('eny',[vector],a.m)
            assert tuple(r(mapped(x)) for x in ('x','y','z'))==tuple(f*x for f,x in zip((a.beta**3,a.beta**2,a.beta**2),inputs));cases+=1
            for nl,nt in ((mu,mu),(mu+1,mu),(mu,mu+1)):
                actual=run('enr',[identity,changed,*map(c,(L,T,nl,nt,*inputs))],a.m)
                wanted=all(n*f*x==o*x for n,f,o,x in zip((nl,nt,nt),(a.beta**3,a.beta**2,a.beta**2),(L,T,T),inputs))
                assert actual==wanted;cases+=1
        # Equal force/acceleration rescaling preserves coefficients: a distinct definition need not imply a difference.
        scale=mapvalue(a,(2,3,3))
        assert run('enr',[scale,scale,*map(c,(L,T,L,T,1,2,3))],a.m);cases+=1
        choices=['a','b',identity,changed,'other'];vals=a.values(CONVENTION)+choices+[c(mu),c(mu)]
        assert run('enu',vals,a.m|{'ens':lambda *xs:True})==(speed!=0);cases+=1
        assert not run('enu',vals,a.m|{'ens':lambda *xs:False});cases+=1
        reject(lambda:run('ens',[identity,changed,*map(c,(L,T,mu,mu))],a.m));cases+=1
    return dict(cases=cases,native_three_component_maps_and_same_history=True,zero_speed_and_compensated_redefinitions=True,full_real_response_domain_refused=True)

@lru_cache(None)
def selection_checks():
    a=prior.model();identity=mapvalue(a,(1,1,1));changed=mapvalue(a,(2,3,3));values=a.values(CONVENTION)+['a','b',identity,changed,'other'];calls=[]
    def choice(*xs):
        method,description,*rest=xs;selector=json.loads(description.syntax)['symbol'];setting,mapper,alternative=rest[:-2],rest[-2],rest[-1]
        probe=a.point([1,2,3,0]);expected=identity if method=='a' else changed
        # The interpreter wraps functions with sort checks; test their distinguishing outputs, not Python identity.
        calls.append((method,selector));return (method,selector) in (('a','enp'),('b','enq')) and a.key(setting)==a.key(a.values(CONVENTION)) and a.key(mapper(probe))==a.key(expected(probe)) and alternative=='other'
    def differs(*xs):return xs[0]=='b' and json.loads(xs[1].syntax)['symbol']=='enq' and a.key(xs[2:-1])==a.key(a.values(CONVENTION)) and xs[-1]=='other'
    mm={'eiszc':choice,'eiszd':differs,'eisze':lambda *xs:xs==('tenth','case','other')}
    assert run('ent',values,mm);cases=1
    assert set(calls)=={('a','enp'),('b','enq')};cases+=1
    for symbol in mm:assert not run('ent',values,mm|{symbol:lambda *xs:False});cases+=1
    for pos in (0,1,2,3,4):
        altered=values.copy();altered[-5+pos]=['b','a',changed,identity,'case'][pos]
        assert not run('ent',altered,mm);cases+=1
    for symbol in mm:reject(lambda:run('ent',values,mm|{symbol:forbidden}));cases+=1
    return dict(cases=cases,same_46_roles_and_both_quantity_selectors=True,scope_and_intensional_change_independent_of_mass_result=True)

@lru_cache(None)
def caution_checks():
    cases=0
    # A theory must contain an electron-motion law, independently of its truth.
    rows={'eisvd':{('a','a','a','case')},'vd':{('b','case')},'eisxn':{('b','a','a','case')},'eiszf':{('a','b','case')}}
    cases+=perturb(lambda m:run('en2',['a','case'],m,True),{n:relation(rs) for n,rs in rows.items()},rows)
    meta={'zrcactor':lambda:FunctionValue(('individual',),'individual',lambda x:'a'),'zrcleft':lambda:FunctionValue(('individual',),'individual',lambda x:'a'),'zrcright':lambda:FunctionValue(('individual',),'individual',lambda x:'b'),'zrctopic':lambda:FunctionValue(('individual',),'individual',lambda x:'a')}
    mm=meta|{'eiszg':lambda *xs:xs==('b','a','a','b','case'),'en2':lambda *xs:xs in (('a','case'),('b','case'))}
    assert run('en3',['a','b','a','b','case'],mm,True);cases+=1
    for sym in ('eiszg','en2'):assert not run('en3',['a','b','a','b','case'],mm|{sym:lambda *xs:False},True);cases+=1
    assert not run('en3',['a','b','a','a','case'],mm,True);cases+=1
    # Keep the actual aspect quantifiers. One omitted relevant aspect invalidates care.
    mm={'en3':lambda *xs:xs==('a','b','a','b','case'),'seqm':lambda *xs:True,'eiszh':lambda act,aspect,ctx:act=='b' and ctx=='case','eiszi':lambda *xs:xs[0:2]==('a','b') and xs[-1]=='case'}
    for d in boundary('en4')['declarations']:
        if d['kind']=='primitive' and d['name'].startswith('zrc') and isinstance(d['result'],dict):
            typ=d['result'];mm[d['name']]=lambda typ=typ:FunctionValue(tuple(typ['parameters']),typ['result'],forbidden)
    assert run('en4',['a','b'],mm,True);cases+=1
    for missing in ('a','b'):
        assert not run('en4',['a','b'],mm|{'eiszi':lambda who,act,aspect,ctx:aspect!=missing},True);cases+=1
    for sym in ('en3','seqm','eiszh'):assert not run('en4',['a','b'],mm|{sym:lambda *xs:False},True);cases+=1
    for care in (False,True):
        for degree in (False,True):
            mm={'en4':lambda *xs:Content(('case','other'),(care,False)),'eiszj':lambda who,act,desc,standard,ctx:degree and (who,act,json.loads(desc.syntax)['symbol'],standard,ctx)==('a','b','en4','a','case')}
            assert run('en5',['a','b'],mm,True)==(care and degree);cases+=1
    # Requirement names the same actor/activity and quoted strong procedure; no actual compliance is executed.
    row=('a','a','a','b','en5',True,'case')
    rows={'zrcmust':{row}}
    mm={'en3':lambda *xs:xs==('a','b','a','b','case'),'en5':forbidden,'zrcmust':relation({row})}
    cases+=perturb(lambda m:run('en6',[],m,True),mm,rows)
    # Connectives evaluate their known inputs eagerly; false antecedents need no true obligation, while unknown inputs still reject.
    assert run('en6',[],{'en3':lambda *xs:False,'zrcmust':lambda *xs:False,'en5':forbidden},True);cases+=1
    return dict(cases=cases,theory_law_membership_and_different_comparison_targets=True,all_relevant_aspects_and_high_degree=True,requirement_not_actual_compliance_or_activity_existence=True)

@lru_cache(None)
def presentation_checks():
    rows={'uh':{('eiszl','author','enw','tenth','case'),('eiszm','author','en6','tenth','case')},'zdg':{('eiszl','author','enw','tenth','case')},'eiswm':{('eiszl','author','eisy3','enb','paper','case')},'zc':{('eiszm','author','enw','en6','tenth','case')},'ue':{('eiszl','eiszm','case')}}
    mm={n:relation(rs) for n,rs in rows.items()}|{n:forbidden for n in ('enw','en6','enb')}
    cases=perturb(lambda m:run('en7',[],m),mm,rows)
    rows={'eir3':{('eiszl','author','paper','eoa','case')},'ue':{('eisy6','eiszl','case')}}
    cases+=perturb(lambda m:run('eob',[],m),{n:relation(rs) for n,rs in rows.items()}|{'eoa':forbidden},rows)
    return dict(cases=cases,obviousness_backward_reference_author_inference_order=True,quoted_claim_and_requirement_not_executed=True)

def scalarize(x):
    if x=='number':return 'individual'
    if isinstance(x,list):return [scalarize(y) for y in x]
    if not isinstance(x,dict):return x
    if x.get('kind')=='call' and x.get('symbol')=='bb':return dict(kind='call',symbol='jecczero',arguments=[])
    return {k:scalarize(v) for k,v in x.items()}

@lru_cache(None)
def binding_checks():
    cases=0;doc=collapse(scalarize(boundary('env')))
    doc['declarations'].append(dict(kind='primitive',name='jecczero',parameters=[],result='individual'))
    d=next(x for x in doc['declarations'] if x['name']=='env');names=[p['name'] for p in d['parameters']];base=[dict(kind='variable',name=n) for n in names]
    starts=[x for x in walk(d['body']) if x.get('kind') in ('exists','forall')]
    # Independent contract: both occurrences of the choice bind the five public roles in order.
    branches=d['body']['arguments'][1]['arguments'];exist,universal=branches
    def peel(node,count,kind):
        bs=[]
        for _ in range(count):assert node['kind']==kind;bs.append(dict(kind='variable',name=node['variable']));node=node['body']
        return bs,node
    ev,eb=peel(exist,5,'exists');uv,ub=peel(universal,5,'forall')
    assert eb==dict(kind='call',symbol='ent',arguments=base+ev)
    assert ub['arguments'][0]==dict(kind='call',symbol='ent',arguments=base+uv)
    cv,cb=peel(ub['arguments'][1],2,'exists')
    assert cb==dict(kind='call',symbol='enu',arguments=base+uv+cv);cases+=1
    groups=[(exist,5,'exists',d['parameters'],'ent'),(universal,5,'forall',d['parameters'],'ent'),(ub['arguments'][1],2,'exists',d['parameters']+[dict(name=x['name'],sort=('situation' if i==4 else 'individual')) for i,x in enumerate(uv)],'enu')]
    for start,count,kind,parameters,target in groups:
        for pivot in range(count):
            f,dd,slots,name,b=lifted(doc,'env',pivot,count,kind,(start,parameters));env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']};special='other' if (kind=='forall' and pivot==4) or (kind=='exists' and count==5 and pivot==4) else 'b'
            targetcall=next(x for x in walk(b) if x.get('kind')=='call' and x.get('symbol')==target)
            row=tuple((env|{name:special})[x['name']] for x in targetcall['arguments'])
            for accept in (False,True):
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}
                if kind=='forall':mm|={'ent':lambda *xs:xs==row,'enu':lambda *xs:accept}
                else:mm[target]=lambda *xs:accept and xs==row
                want=accept
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=50000)[0]['value']==want;cases+=1
    # Evaluate the intact conditional in the explicitly collapsed diagnostic domain.
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jeccfixed'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol='env',arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))];doc['declarations'].sort(key=lambda x:x['kind']!='primitive')
    fixed={n:lambda x=('case' if p['sort']=='situation' else 'a'):x for n,p in zip(slots,d['parameters'])}
    for baseline,nonempty,allgood,want in [(False,False,False,True),(True,False,True,False),(True,True,True,True),(True,True,False,False)]:
        mm=fixed|{'jecczero':lambda:'a','tc':lambda:'a','eisxt':lambda:'b','soy':lambda *xs:'a','shv':lambda *xs:'a','bg':lambda *xs:True,'emf':lambda *xs:baseline,'ent':lambda *xs:nonempty and xs[-1]=='other','enu':lambda *xs:allgood or xs[-7]=='a'}
        assert evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in doc['declarations'] if x['kind']=='primitive'},max_steps=100000)[0]['value']==want;cases+=1
    # Full actual setting remains outside choices and mass candidates.
    native=next(x for x in core()['declarations'] if x['name']=='enw');node=native['body']['body'];bindings=[]
    for _ in BOUND+EXTRA_MASS:assert node['kind']=='forall';bindings.append(node['variable']);node=node['body']
    mapping=dict(zip([n for n,t in BOUND+EXTRA_MASS],bindings));var=lambda n:dict(kind='variable',name=n);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
    fixed={'frame':constant('ra'),'event':constant('eisxv'),'context':var(native['body']['variable']),'electricconversion':dict(kind='call',symbol='bb',arguments=[dict(kind='number',value='1')])}
    # Rational literal shape is taken from the independently fixed unit definition.
    expected=[fixed[n] if n in fixed else var(mapping['oldpoint' if n=='point' else n]) for n,t in CONVENTION]
    actual=node['arguments'];assert node['symbol']=='env' and len(actual)==46
    for i,(n,t) in enumerate(CONVENTION):
        if n=='electricconversion':assert actual[i]['kind']=='call' and actual[i]['symbol']=='bb'
        else:assert actual[i]==expected[i]
    cases+=1
    return dict(cases=cases,all_five_choices_and_both_mass_candidates_bound=True,nonempty_all_relevant_alternatives_not_one_successful_example=True,independent_46_role_contract_and_conditional_scope=True,finite_collapsed_domains_not_physical_truth=True)

@lru_cache(None)
def source_record():
    unit=json.loads(read(INVENTORY))['units'][258];assert unit['id']=='einstein-1905:u0259' and digest(unit['text'].encode())==unit['text_sha256']
    return dict(version='einstein-electron-convention-caution-reading-v1',unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],math=[],source_nonblank_characters=len(re.sub(r'\s','',unit['text'])),facsimile_pages=[919],observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==427 and after.document['statements'][:426]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[425])==selection_binding(before,[425]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_reference_constants=len(REFERENCES),new_statements=1,all_426_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numerical',numerical_checks),('selection',selection_checks),('caution',caution_checks),('presentation',presentation_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_convention_caution.py','scripts/check_electron_convention_caution.py','tests/test_electron_convention_caution.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='alternative_definitions_and_care_requirement_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
