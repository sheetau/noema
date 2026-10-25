"""Check the physical and hypothetical roles without certifying real domains."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_mass_rewrite as prior
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_force_measurement import *

DOC='docs/electron-force-measurement-v1.md'
DEPENDENCIES=('reports/electron-mass-rewrite-v1.json','reports/electric-action-v1.json')
Model=prior.Model;fn=prior.fn;sort=prior.sort;forbidden=prior.forbidden;reject=prior.reject
CONSTANTS=prior.CONSTANTS
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,'instrument','spring','operation','force_record','acceleration_unit']))
BOUNDS={'ely':{'ek63','eibs'},'el2':{'elz'},'el3':{'el2'},'el4':{'el3'},'el5':{'el4'},'el6':{'ely','el5'},'el7':{'el6'},'ema':{'ek63','ely'},'emb':{'ek63','el7'},'emc':{'ely','ejwb'},'emd':{'emc','sepi'},'eme':{'emd'},'emf':{'emc'},'emg':{'emc','emd','emf'}}
@lru_cache(None)
def core():return parse(read(CORE))
def walk(node):
    if isinstance(node,dict):
        yield node
        for v in node.values():yield from walk(v)
    elif isinstance(node,list):
        for v in node:yield from walk(v)
@lru_cache(None)
def boundary(root,mode='boundary'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in prior.prior.prior.base.BOUNDS|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='calibration_samples':
        assert root=='elz'
        def substitute(node,name,replacement):
            if isinstance(node,dict):
                if node==dict(kind='variable',name=name):return deepcopy(replacement)
                return {k:substitute(v,name,replacement) for k,v in node.items()}
            if isinstance(node,list):return [substitute(x,name,replacement) for x in node]
            return node
        def expand(node):
            if isinstance(node,dict):
                if node.get('kind')=='forall' and node['sort']==sort(R):
                    terms=[expand(substitute(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in ('jfmnegative','jfmzero','jfmpositive')]
                    return dict(kind='and',arguments=[terms[0],dict(kind='and',arguments=terms[1:])])
                return {k:expand(v) for k,v in node.items()}
            if isinstance(node,list):return [expand(v) for v in node]
            return node
        doc=expand(doc)
        doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=sort(R)) for n in ('jfmnegative','jfmzero','jfmpositive')]
    return doc
@lru_cache(None)
def fixture(root,mode='boundary'):
    doc=deepcopy(boundary(root,mode));d=next(x for x in doc['declarations'] if x['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jfmarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expression=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jfmpoint',parameters=[],result='situation'));expression=dict(kind='evaluate',content=expression,situation=dict(kind='call',symbol='jfmpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jfmcapture',parameters=[d['result']],result='truth'));expression=dict(kind='call',symbol='jfmcapture',arguments=[expression])
    doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expression)];return doc,slots
def run(root,values,m,mode='boundary'):
    doc,slots=fixture(root,mode);assert len(slots)==len(values);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jfmpoint':lambda:'case','jfmcapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,values)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result
def force_model():
    a=Model();a.by['forcerecord']='force_record';a.by['force']=a.point([a.r(a.by['charge'])*a.r(a.by['newelectric'](axis)(*map(a.c,(0,0,0,0)))) for axis in ('x','y','z')]+[0]);return a

@lru_cache(None)
def force_checks():
    a=force_model();key=a.key;c,r=a.c,a.r;new=a.new();new.update(carrier=a.by['matter'],forcerecord='force_record',fieldunit=a.by['electricunit'],force=a.by['force'],conversion=c(1),electric=a.point([r(new['electricfield'](axis)(*map(c,(0,0,0,0)))) for axis in ('x','y','z')]+[0]))
    expected=key([new[n] for n,t in ACTION]);pair=key(a.values());seen=[]
    def action(*xs):seen.append(key(xs));return key(xs)==expected
    mm=a.m|{'ek63':lambda *xs:key(xs)==pair,'eibs':action}
    assert run('ely',a.values(FORCE),mm) and seen==[expected];cases=1
    for n in ('ek63','eibs'):assert not run('ely',a.values(FORCE),mm|{n:lambda *xs:False});reject(lambda:run('ely',a.values(FORCE),mm|{n:forbidden}));cases+=2
    def different(t):
        if t==sort(R):return c(37)
        if t=='truth':return False
        return fn(t,lambda *xs:different(t['result']))
    for i,(name,t) in enumerate(FORCE):
        values=a.values(FORCE);values[i]='other' if t in ('a','d') else Q(37) if t=='b' else different(sort(t))
        assert not run('ely',values,mm),name;cases+=1
    numeric=[a.by['charge'],new['electric'],c(1),a.by['force']]
    assert run('eibr',numeric,a.m);cases+=1
    for i in range(3):
        bad=list(a.pv(a.by['force']));bad[i]+=1
        assert not run('eibr',numeric[:3]+[a.point(bad)],a.m);cases+=1
    target={n:a.by[n] for n,t in TARGET};target['frame']='comoving';expected_target=key([target[n] for n,t in TARGET])
    mm={'ely':lambda *xs:key(xs)==key(a.values(FORCE)),'el5':lambda *xs:key(xs)==expected_target}
    assert run('el6',a.values(FORCE),mm);cases+=1
    for n in mm:assert not run('el6',a.values(FORCE),mm|{n:lambda *xs:False});cases+=1
    return dict(cases=cases,all_44_force_roles_and_current_comoving_field=True,native_signed_three_component_force_relation=True,same_source_record_vector_units_and_context_for_measurement=True)

@lru_cache(None)
def calibration_checks():
    a=Model();c,r=a.c,a.r;domain=fn(sort(DOMAIN),lambda x:-2<r(x)<2);cases=0
    mm=a.m|{n:lambda value=value:c(value) for n,value in [('jfmnegative',-1),('jfmzero',0),('jfmpositive',1)]}
    for f,want in [(lambda x:2*x,True),(lambda x:x+x**3,True),(lambda x:-x,False),(lambda x:0,False),(lambda x:2*x+1,False)]:
        response=fn(sort(F),lambda x:fvalue(f,r(x),c))
        assert run('elz',[domain,response],mm,'calibration_samples')==want;cases+=1
    response=fn(sort(F),lambda x:c(2*r(x)));nozero=fn(sort(DOMAIN),lambda x:r(x)!=0)
    assert not run('elz',[nozero,response],mm,'calibration_samples');cases+=1
    reject(lambda:run('elz',[domain,response],mm));cases+=1
    reject(lambda:run('elz',[domain,fn(sort(F),forbidden)],mm,'calibration_samples'));cases+=1
    by=dict(instrument='instrument',element='spring',frame='comoving',axis='x',lengthunit=a.by['lengthunit'],forceunit=a.by['forceunit'],range=domain,response=response,context='other');values=[by[n] for n,t in GAUGE]
    rows={'zjg':('spring','instrument','other'),'x4':('instrument','comoving','other'),'eisyr':a.key([by[n] for n,t in PRIMITIVES['eisyr'][0]]),'eisys':a.key(values),'elz':a.key([domain,response])}
    models={n:lambda *xs,n=n:a.key(xs)==rows[n] for n in rows}
    assert run('el2',values,models);cases+=1
    for n in rows:assert not run('el2',values,models|{n:lambda *xs:False});reject(lambda:run('el2',values,models|{n:forbidden}));cases+=2
    changed=values.copy();changed[1]='instrument';assert not run('el2',changed,{n:lambda *xs:True for n in rows});cases+=1
    return dict(cases=cases,linear_and_nonlinear_sample_calibrations=True,reversed_constant_shifted_or_unrooted_scales_distinguished=True,elastic_element_readout_calibration_part_and_rest_separate=True,full_real_calibration_refused=True)
def fvalue(f,x,c):return c(f(x))

@lru_cache(None)
def trial_checks():
    a=Model();c,r=a.c,a.r;key=a.key;cases=0
    by=dict(matter='matter',forcerecord='force_record',frame='comoving',event='event',forceunit=a.by['forceunit'],lengthunit=a.by['lengthunit'],force=a.point((2,-4,0,0)),context='case',instrument='instrument',element='spring',axis='x',operation='operation',alternative='other',range=fn(sort(DOMAIN),lambda x:-3<r(x)<3),response=fn(sort(F),lambda x:c(2*r(x))),deflection=c(1))
    values=[by[n] for n,t in TRIAL];gauge=by|{'context':'other'};trial=by|{'source':'case'}
    rows={'el2':key([gauge[n] for n,t in GAUGE]),'eisyt':key([trial[n] for n,t in PRIMITIVES['eisyt'][0]])}
    possible=lambda *xs:xs==('operation','matter','case','other')
    mm=a.m|{n:lambda *xs,n=n:key(xs)==rows[n] for n in rows}|{'zrdpossible':lambda:fn(sort('h[a a d d] c'),possible)}
    assert run('el3',values,mm);cases+=1
    for n in rows:assert not run('el3',values,mm|{n:lambda *xs:False});reject(lambda:run('el3',values,mm|{n:forbidden}));cases+=2
    assert not run('el3',values,mm|{'zrdpossible':lambda:fn(sort('h[a a d d] c'),lambda *xs:False)});cases+=1
    for name,replacement in [('deflection',c(2)),('axis','y'),('context','other'),('alternative','case'),('frame','frame'),('forcerecord','other')]:
        changed=values.copy();changed[[n for n,t in TRIAL].index(name)]=replacement;assert not run('el3',changed,mm),name;cases+=1
    # Correct signed readings for each component, without source-state rest.
    for axis,delta in [('x',1),('y',-2),('z',0)]:
        by.update(axis=axis,deflection=c(delta));gauge=by|{'context':'other'};trial=by|{'source':'case'};rows.update(el2=key([gauge[n] for n,t in GAUGE]),eisyt=key([trial[n] for n,t in PRIMITIVES['eisyt'][0]]))
        assert run('el3',[by[n] for n,t in TRIAL],mm);cases+=1
    return dict(cases=cases,source_force_and_possible_result_not_conflated=True,physical_possibility_and_actual_comparison_separate=True,three_signed_force_readings_with_shared_units=True)

@lru_cache(None)
def convention_checks():
    a=force_model();c,r=a.c,a.r;key=a.key;cases=0
    a.by.update(accelerationunit='acceleration_unit',accelerationscale=Q(2),lengthscale=Q(18),timescale=Q(3),massscale=Q(5),forcescale=Q(10))
    physical=key(a.values(FORCE));units=('acceleration_unit',Q(1),Q(0),Q(-2),Q(2),'case');convention=(a.by['matter'],'comoving','frame',a.by['event'],a.by['forceunit'],'acceleration_unit','case')
    mm=a.m|{'ad':lambda x,y:x*y,'ely':lambda *xs:key(xs)==physical,'ejwb':lambda *xs:xs==units,'zraconvention':lambda *xs:xs==convention}
    assert run('emc',a.values(CONVENTION),mm);cases+=1
    for name in ('accelerationscale','lengthscale','timescale','massscale','forcescale'):
        values=a.values(CONVENTION);i=[n for n,t in CONVENTION].index(name);values[i]+=1
        # Accept the physical boundary independently, to test the scale algebra.
        assert not run('emc',values,mm|{'ely':lambda *xs:True,'ejwb':lambda *xs:True});cases+=1
    for n in ('ely','ejwb','zraconvention'):assert not run('emc',a.values(CONVENTION),mm|{n:lambda *xs:False});cases+=1
    L=r(a.by['mass'])*a.beta**3;T=r(a.by['mass'])*a.beta**2;coeff=[c(L),c(T)]
    mm=a.m|{'emc':lambda *xs:key(xs)==key(a.values(CONVENTION))}
    assert run('emf',a.values(CONVENTION)+coeff,mm);cases+=1
    for wrong in [(L+1,T),(L,T+1),(L,r(a.by['mass'])*a.beta)]:assert not run('emf',a.values(CONVENTION)+list(map(c,wrong)),mm);cases+=1
    for axis in range(3):
        force=list(a.pv(a.by['force']));force[axis]+=1;values=a.values(CONVENTION);values[[n for n,t in CONVENTION].index('force')]=a.point(force)
        assert not run('emf',values+coeff,mm|{'emc':lambda *xs:True});cases+=1
    accepted=key(a.values(CONVENTION)+coeff)
    for allowed in (False,True):assert run('emd',a.values(CONVENTION)+coeff,mm|{'sepi':lambda *xs:allowed})==allowed;cases+=1
    for permitted in ((),((L,T),),((L,T),(L+1,T+1))):
        question=run('eme',a.values(CONVENTION),{'emd':lambda *xs:key(xs[:-2])==key(a.values(CONVENTION)) and tuple(map(r,xs[-2:])) in permitted});assert isinstance(question,QuestionValue);cases+=1
        for candidate in ((L,T),(L+1,T+1),(0,0)):assert question.function(*map(c,candidate))==(candidate in permitted);cases+=1
    question=run('eme',a.values(CONVENTION),{'emd':forbidden});reject(lambda:question.function(*coeff));cases+=1
    reject(lambda:run('sepi',[c(5),c(3),c(a.beta),a.by['mass'],*coeff],a.m));cases+=1
    return dict(cases=cases,acceleration_dimension_and_both_scale_identities=True,actual_force_and_coordinate_acceleration_in_same_convention=True,longitudinal_beta_cubed_transverse_beta_squared=True,coefficient_identity_not_replaced_by_one_zero_case=True,question_can_have_zero_one_or_multiple_candidates=True)

@lru_cache(None)
def binding_checks():
    cases=0
    def individualize(node):
        if node=='number':return 'individual'
        if isinstance(node,dict):return {k:individualize(v) for k,v in node.items()}
        if isinstance(node,list):return [individualize(x) for x in node]
        return node
    # Independently check call arguments against public role lists. The actual
    # argument AST is then used only for two-value binder diagnostics.
    for root,target,roles,count in [('el5','el4',TARGET+[('instrument','a'),('element','a')],2),('el7','el6',FORCE,2)]:
        doc=collapse(individualize(boundary(root)));d=next(x for x in doc['declarations'] if x['name']==root);body=d['body'];names=[]
        for _ in range(count):names.append(body['variable']);body=body['body']
        expected=[dict(kind='variable',name=p['name']) for p in d['parameters']]+[dict(kind='variable',name=n) for n in names]
        assert body['symbol']==target and body['arguments']==expected and len(expected)==len(roles);cases+=1
        for pivot in range(count):
            f,d,slots,var,b=lifted(doc,root,pivot,count,'exists');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            row=tuple((env|{var:'b'})[x['name']] for x in b['arguments'])
            for succeeds in (False,True):
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{target:lambda *xs:xs==row and succeeds}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==succeeds;cases+=1
    doc=collapse(boundary('el4'));d=next(x for x in doc['declarations'] if x['name']=='el4');starts=[x for x in walk(d['body']) if x.get('kind')=='exists' and len([y for y in walk(x) if y.get('kind')=='exists'])==len(WITNESSES)]
    assert len(starts)==3
    for start,axis in zip(starts,ROLES[:3]):
        body=start;names=[]
        for _ in WITNESSES:names.append(body['variable']);body=body['body']
        mapping=dict(zip((n for n,t in TARGET+[('instrument','a'),('element','a')]),(p['name'] for p in d['parameters'])))|dict(zip((n for n,t in WITNESSES),names))
        expected=[dict(kind='call',symbol=axis,arguments=[]) if n=='axis' else dict(kind='variable',name=mapping[n]) for n,t in TRIAL]
        assert body['symbol']=='el3' and body['arguments']==expected;cases+=1
        for pivot in range(len(WITNESSES)):
            f,dd,slots,var,b=lifted(doc,'el4',pivot,len(WITNESSES),'exists',(start,d['parameters']));env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']};chosen='other' if WITNESSES[pivot][1]=='d' else 'b'
            call=next(x for x in walk(b) if x.get('kind')=='call' and x.get('symbol')=='el3');row=tuple((env|{var:chosen})[x['name']] if x['kind']=='variable' else 'a' for x in call['arguments'])
            for succeeds in (False,True):
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{axis:lambda:'a','el3':lambda *xs:xs==row and succeeds}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==succeeds;cases+=1
    # Candidate values are inside the question; all physical settings remain
    # its unchanged outer parameters, in their independent public role order.
    d=next(x for x in core()['declarations'] if x['name']=='eme');f=d['body']['function'];call=f['body']
    assert call['symbol']=='emd' and call['arguments']==[dict(kind='variable',name=p['name']) for p in d['parameters']+f['parameters']];cases+=1
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jfmunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    for root in ('ema','emb'):
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jfmunit',parameters=[],result='individual'));doc['declarations'].sort(key=lambda x:x['kind']!='primitive');doc=extract_document(doc,roots=[root],statement_indices=[]).document
        d=next(x for x in doc['declarations'] if x['name']==root);body=d['body']['body'];names=[]
        for _ in BOUND:names.append(body['variable']);body=body['body']
        mapping=dict(zip((n for n,t in BOUND),names));variable=lambda n:dict(kind='variable',name=n);constant=lambda n:dict(kind='call',symbol=n,arguments=[])
        fixed={'frame':constant('ra'),'event':constant('eisxv'),'electricconversion':constant('jfmunit'),'context':variable(d['body']['variable'])}
        expected=[fixed[n] if n in fixed else variable(mapping['oldpoint' if n=='point' else n]) for n,t in PAIR]
        assert body['kind']=='implies' and body['arguments'][0]==dict(kind='call',symbol='ek63',arguments=expected)
        if root=='ema':
            witness=body['arguments'][1];extra=[]
            for _ in range(2):extra.append(variable(witness['variable']));witness=witness['body']
            assert witness==dict(kind='call',symbol='ely',arguments=expected+extra);cases+=1
            continue
        assert body['arguments'][1]==dict(kind='call',symbol='el7',arguments=expected);cases+=1
        for pivot in range(len(BOUND)):
            f,dd,slots,var,b=lifted(doc,root,pivot,len(BOUND),'forall');env={p['name']:'case' if p['sort']=='situation' else 'a' for p in dd['parameters']}
            calls={x['symbol']:x['arguments'] for x in walk(b) if x.get('kind')=='call' and x.get('symbol') in ('ek63','el7')}
            def row(call,value):return tuple((env|{var:value})[x['name']] if x['kind']=='variable' else 'a' for x in call)
            for accepted,want in [(('a','b'),True),(('a',),False)]:
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,dd['parameters'])}|{n:lambda:'a' for n in ('ra','eisxv','jfmunit')}
                mm|={n:lambda *xs,n=n:xs in {row(calls[n],value) for value in (('a','b') if n=='ek63' else accepted)} for n in ('ek63','el7')}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives={x['name']:mm.get(x['name'],forbidden) for x in f['declarations'] if x['kind']=='primitive'},max_steps=25000)[0]['value']==want,(pivot,accepted);cases+=1
    for root in ('ema','emb'):reject(lambda:run(root,[],{'ek63':lambda *xs:True,'ely':lambda *xs:True,'el7':lambda *xs:True}));cases+=1
    return dict(cases=cases,same_instrument_element_and_three_independent_trials=True,every_operation_result_range_curve_and_deflection_witness_checked=True,force_record_and_vector_share_one_witness_pair=True,all_38_current_setting_binders_checked=True,question_preserves_outer_setting_roles=True,full_real_and_function_domains_refused=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==423 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[422])==selection_binding(before,[422]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/electron-mass-rewrite-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),new_statements=0,all_423_prior_statements_and_meanings_preserved=True)
def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('force',force_checks),('calibration',calibration_checks),('trials',trial_checks),('convention',convention_checks),('bindings',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'scripts/compose_electron_force_measurement.py','scripts/check_electron_force_measurement.py','tests/test_electron_force_measurement.py'}
    for path in DEPENDENCIES:paths.update(json.loads(read(path))['source_sha256'])
    return dict(status='same_electron_force_measurement_and_mass_candidates_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
