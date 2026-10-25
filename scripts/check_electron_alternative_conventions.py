"""Check changed frame definitions without certifying every alternative choice."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_directional_masses as prior
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_alternative_conventions import *

DOC='docs/electron-alternative-conventions-v1.md';SOURCE='data/einstein-electron-alternative-conventions-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf'
DEPENDENCIES=('reports/electron-directional-masses-v1.json','reports/electron-transformed-dynamics-v1.json','reports/mass-coefficients-v1.json')
CONSTANTS=prior.CONSTANTS;PEOPLE=prior.PEOPLE;NUM=prior.NUM
forbidden=prior.forbidden;reject=prior.reject;walk=prior.walk
BOUNDS={'eng':{'emc'},'enh':{'eng','end'},'eni':{'eng'},'enj':{'eng','enh','eni'},'enk':{'emc','ek7c'},'enl':{'enk','eng','eni'},'enm':{'eng','emc'},'eno':{'eng','emc'}}

@lru_cache(None)
def core():return parse(read(CORE))
@lru_cache(None)
def boundary(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=NUM|BOUNDS.get(root,set())
    if mode=='binding':cuts|={'seph','ba'}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='probe':
        assert root=='end';d=next(x for x in doc['declarations'] if x['name']==root)
        # Keep the real native matrix-equation body; instantiate its six inputs.
        head=d['body'];quantifier=next(x for x in walk(head) if x.get('kind')=='forall');body=quantifier;parameters=[]
        for _ in SIX:parameters.append(dict(name=body['variable'],sort=body['sort']));body=body['body']
        def replace(x):
            if x==quantifier:return body
            if isinstance(x,dict):return {k:replace(v) for k,v in x.items()}
            if isinstance(x,list):return [replace(v) for v in x]
            return x
        d['body']=replace(head);d['parameters']+=parameters
    return doc
@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jacslot'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots
def run(root,values,m,mode='boundary'):
    doc,slots=fixture(root,mode);assert len(values)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(speed=3,A=1):
    a=prior.prior.Model(speed,A);c,r=a.c,a.r
    a.by.update(forcerecord='force_record',force=a.point([r(a.by['charge'])*r(a.by['newelectric'](axis)(*map(c,(0,0,0,0)))) for axis in ('x','y','z')]+[0]),accelerationunit='acceleration_unit',accelerationscale=Q(1),alternative='other')
    return a

@lru_cache(None)
def numerical_checks():
    a=model();c,r=a.c,a.r;cases=0
    # Scaling a physical quantity's numerical definition is not automatically a unit change.
    rows=[((8,6,1,1,4,3,2,2),True),((8,6,2,2,2,2,8,6),True),((8,6,2,3,1,1,16,18),True),((8,6,1,1,4,3,3,2),False),((8,6,1,1,4,3,2,3),False),((8,6,0,1,4,3,0,2),False),((8,6,1,1,-4,3,-2,2),False),((8,6,1,1,0,3,2,2),False)]
    for values,want in rows:assert run('enf',list(map(c,values)),a.m)==want;cases+=1
    for values,want in [((4,4,4),True),((4,5,4),False),((4,4,5),False),((0,0,0),True),((-2,-2,-2),True)]:assert run('ene',list(map(c,values)),a.m)==want;cases+=1
    # Instantiate the actual universally quantified body on distinguishing inputs.
    for L,T in ((4,4),(5,4),(4,5)):
        for accelerations in ((0,0,0),(1,0,0),(0,1,0),(0,0,1),(2,-3,5)):
            force=tuple(4*x for x in accelerations)
            wanted=all(m*x==f for m,x,f in zip((L,T,T),accelerations,force))
            assert run('end',list(map(c,(4,L,T,*accelerations,*force))),a.m,'probe')==wanted;cases+=1
    reject(lambda:run('end',list(map(c,(4,4,4))),a.m));cases+=1
    for values,want in [((8,6,4,4),True),((8,6,8,6),False),((8,6,8,7),True),((8,6,9,6),True)]:assert run('enn',list(map(c,values)),a.m)==want;cases+=1
    return dict(cases=cases,proportional_redefinitions_can_preserve_coefficients=True,zero_input_not_coefficient_identification=True,native_matrix_body_probes_not_full_real_proof=True,full_real_domain_refused=True)

@lru_cache(None)
def physical_checks():
    cases=0
    for speed in (0,3):
        a=model(speed);c,r,key=a.c,a.r,a.key;mu=r(a.by['mass']);L=mu*a.beta**3;T=mu*a.beta**2
        choice=(a.by['matter'],'comoving','comoving',a.by['event'],a.by['forceunit'],'acceleration_unit','other')
        mm=a.m|{'emc':lambda *xs:key(xs)==key(a.values(CONVENTION)),'zraconvention':lambda *xs:xs==choice}
        assert run('eng',a.values(ALT),mm);cases+=1
        for position in range(len(choice)):
            wrong=list(choice);wrong[position]='case' if position==6 else 'wrong'
            assert not run('eng',a.values(ALT),mm|{'zraconvention':lambda *xs:xs==tuple(wrong)});cases+=1
        for symbol in ('emc','zraconvention'):reject(lambda:run('eng',a.values(ALT),mm|{symbol:forbidden}));cases+=1
        permission=lambda *xs:key(xs)==key(a.values(ALT))
        mm=a.m|{'eng':permission,'emc':lambda *xs:key(xs)==key(a.values(CONVENTION))}
        values=a.values(ALT)+[c(mu),c(mu)]
        assert run('eni',values,mm);cases+=1
        for name in ('newax','neway','newaz'):
            changed=values.copy();index=[n for n,t in ALT].index(name);changed[index]=c(r(changed[index])+1)
            assert not run('eni',changed,mm|{'eng':lambda *xs:True});cases+=1
        for axis in range(3):
            force=list(a.pv(a.by['force']));force[axis]+=1;changed=values.copy();changed[[n for n,t in ALT].index('force')]=a.point(force)
            assert not run('eni',changed,mm|{'eng':lambda *xs:True});cases+=1
        for coeff in ((mu+1,mu),(mu,mu+1)):assert not run('eni',a.values(ALT)+list(map(c,coeff)),mm);cases+=1
        comparison=a.values(ALT)+list(map(c,(L,T,mu,mu)))
        assert run('enm',comparison,mm);assert run('eno',comparison,mm)==(speed!=0);cases+=2
        for pos in range(4):
            changed=comparison.copy();changed[-4+pos]=c(r(changed[-4+pos])+1)
            assert not run('enm',changed,mm);cases+=1
        # The same native acceleration transform remains necessary, not a free assignment.
        pair=key(a.values(PAIR));mm=a.m|{'emc':lambda *xs:True,'ek7c':lambda *xs:key(xs)==pair}
        assert run('enk',a.values(CONVENTION),mm);cases+=1
        for name in ('newax','neway','newaz'):
            changed=a.values(CONVENTION);pos=[n for n,t in CONVENTION].index(name);changed[pos]=c(r(changed[pos])+1)
            assert not run('enk',changed,mm|{'ek7c':lambda *xs:True});cases+=1
    return dict(cases=cases,same_k_force_and_actual_k_coordinate_acceleration=True,alternative_adoption_context_and_both_frames_checked=True,old_and_new_pairs_bound_together=True,zero_speed_boundary_preserves_mass=True,native_acceleration_transform_checked=True)

@lru_cache(None)
def connection_checks():
    a=model();values=a.values(ALT);key=a.key;cases=0
    for permitted in (False,True):
        for law in (False,True):
            for consequence in (False,True):
                mm={'eng':lambda *xs:key(xs)==key(values) and permitted,'enk':lambda *xs:key(xs)==key(values[:-1]) and law,'eni':lambda *xs:key(xs)==key(values+[a.by['mass'],a.by['mass']]) and consequence}
                assert run('enl',values,mm)==(not(permitted and law) or consequence);cases+=1
    vals=values+[a.c(4),a.c(5)]
    for permitted in (False,True):
        for implicit in (False,True):
            for explicit in (False,True):
                mm={'eng':lambda *xs:key(xs)==key(values) and permitted,'enh':lambda *xs:key(xs)==key(vals) and implicit,'eni':lambda *xs:key(xs)==key(vals) and explicit}
                assert run('enj',vals,mm)==(not permitted or implicit==explicit);cases+=1
    contracts={'eng':(ALT,{'emc':CONVENTION}),'enh':(ALT+COEFFICIENTS,{'eng':ALT,'end':MASS_PAIR}),'eni':(ALT+COEFFICIENTS,{'eng':ALT,'ene':MASS_PAIR}),'enj':(ALT+COEFFICIENTS,{'eng':ALT,'enh':ALT+COEFFICIENTS,'eni':ALT+COEFFICIENTS}),'enk':(CONVENTION,{'emc':CONVENTION,'ek75':PAIR,'ek7c':PAIR}),'eno':(COMPARISON,{'enm':COMPARISON,'enn':OLD+COEFFICIENTS})}
    for root,(fields,targets) in contracts.items():
        d=next(x for x in core()['declarations'] if x['name']==root);mapping=dict(zip((n for n,t in fields),(p['name'] for p in d['parameters'])));seen=set()
        for call in walk(d['body']):
            if call.get('kind')=='call' and call.get('symbol') in targets:
                symbol=call['symbol'];assert call['arguments']==[dict(kind='variable',name=mapping[n]) for n,t in targets[symbol]];seen.add(symbol)
        assert seen==set(targets);cases+=1
    for root in ('enh','eni'):
        d=next(x for x in core()['declarations'] if x['name']==root);names=dict(zip((n for n,t in ALT+COEFFICIENTS),(p['name'] for p in d['parameters'])));var=lambda n:dict(kind='variable',name=names[n]);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
        call=next(x for x in walk(d['body']) if x.get('kind')=='call' and x.get('symbol')=='seph')
        expected=[var('longitudinal'),var('transverse'),var('newax'),var('neway'),var('newaz')]+[dict(kind='apply',function=var('force'),arguments=[constant(axis)]) for axis in ROLES[:3]]
        assert call['arguments']==expected;cases+=1
    return dict(cases=cases,conditional_law_and_choice_not_unconditional_truth=True,independent_public_contracts_for_same_history_and_units=True)

@lru_cache(None)
def binding_checks():
    doc=collapse(boundary('end','binding'));d=next(x for x in doc['declarations'] if x['name']=='end');start=next(x for x in walk(d['body']) if x.get('kind')=='forall');body=start;bound=[]
    for _ in SIX:bound.append(body['variable']);body=body['body']
    var=lambda n:dict(kind='variable',name=n);mu,L,T=[var(p['name']) for p in d['parameters']];six=[var(n) for n in bound]
    calls=[x for x in walk(body) if x.get('kind')=='call' and x.get('symbol')=='seph']
    assert [x['arguments'] for x in calls]==[[mu,mu,*six],[L,T,*six]];cases=1
    for pivot in range(6):
        f,dd,slots,name,b=lifted(doc,'end',pivot,6,'forall',(start,d['parameters']));env={p['name']:'a' for p in dd['parameters']};env[d['parameters'][1]['name']]='b';env[d['parameters'][2]['name']]='b'
        actual=[x for x in walk(b) if x.get('kind')=='call' and x.get('symbol')=='seph'][1]['arguments']
        bad=tuple((env|{name:'b'})[x['name']] for x in actual)
        for accept,want in [(True,True),(False,False)]:
            mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{'ba':lambda *xs:True,'seph':lambda *xs:accept or xs!=bad}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_six_actual_binders_and_two_independent_coefficients_checked=True,small_domain_diagnostic_not_real_domain_proof=True)

@lru_cache(None)
def source_record():
    unit=json.loads(read(INVENTORY))['units'][258];assert unit['id']=='einstein-1905:u0259' and digest(unit['text'].encode())==unit['text_sha256']
    return dict(version='einstein-electron-alternative-conventions-reading-v1',unit=unit['id'],text=unit['text'],unit_sha256=unit['text_sha256'],range=[0,len(unit['text'])],facsimile_pages=[919],whole_unit_reviewed=False,observations=LIMITS,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})
@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==426 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[423,424,425])==selection_binding(before,[423,424,425]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-directional-masses-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        text=format_graph(core(),style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_general_relations=0,new_statements=0,all_426_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numerical',numerical_checks),('physical',physical_checks),('connections',connection_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_alternative_conventions.py','scripts/check_electron_alternative_conventions.py','tests/test_electron_alternative_conventions.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='same_history_alternative_acceleration_convention_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
