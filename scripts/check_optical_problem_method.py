"""Check universal topic scope, shared method witnesses and inverse reconstruction."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document,Content,FunctionValue,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_field_answer_records import function,question,sequence,field,field_key,method_setup,FS,DOMAIN as PRIOR_DOMAIN
from scripts.check_body_rest_field_method import numbers,CONSTANTS as PRIOR_CONSTANTS,point
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_problem_series_reduction import collapse,SEQ
from scripts.check_clock_site_time import relation,perturb
from scripts.compose_optical_problem_method import *
from scripts.read_optical_problem_method import DOC,READING,build_reading

CONSTANTS=PRIOR_CONSTANTS|{'ri':'case','rd':'author','eirf':'paper','eistk':'scope','eisvp':'method','eisvs':'first','eisvt':'second','eisvu':'third','eisvh':'previous','eisuu':'prioruse'}
DOMAIN=tuple(dict.fromkeys([*PRIOR_DOMAIN,*CONSTANTS.values(),'sourceproblem','fieldproblem','target','otheranswer','solution','wrong','lightsource','wave']))
DEPENDENCIES=('reports/field-answer-records-v1.json','reports/body-rest-field-method-v1.json','reports/problem-series-reduction-v1.json')
BOUNDS={'ekwl':{'ejsn'},'ekwm':{'ekwl','eiag'},'ekwn':{'ekwl','eiah'},'ekwp':{'ekwo'},'ekwq':{'ekv6'},'ekwr':{'ekwq','ekwi','ekwe','ekwf','ekwp','sca'},'ekws':{'ekwr'},'ekwx':{'ekvs'},'ekwy':{'ekvq'}}
PRESENT={'ekww','ekwx','ekwy','ekti','ekwq','ekwm','ekwn','ekw5'}

def forbidden(*xs):raise ValueError('Unknown optical-method input')
def rejects(fn,fragment=None):
    try:fn()
    except ValueError as e:
        if fragment:assert fragment in str(e),str(e)
        else:assert any(s in str(e) for s in ('rational number domain','Finite function domain','sequence domain')),str(e)
    else:raise AssertionError('Expected rejection')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=NUM|{'bg','be','sjd','sje','soy','szi','aa'}|BOUNDS.get(root,set())
    if root in ('ekwz','ekw2','ekw3','ekw4','ekw6','ekww','ekwu','ekwv'):cuts|=PRESENT-{root}
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode.startswith('slot:'):
        doc=collapse(doc)
        def numeric_slots(x):
            if x=='number':return 'individual'
            if isinstance(x,list):return [numeric_slots(v) for v in x]
            if isinstance(x,dict):return {k:numeric_slots(v) for k,v in x.items()}
            return x
        doc=numeric_slots(doc)
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode.startswith('slot:'):
        pivot=int(mode.split(':')[1]);body=d['body'];retained=None
        for i,(n,t) in enumerate(WITNESSES):
            assert body['kind']=='exists'
            if i==pivot:retained={k:body[k] for k in ('kind','variable','sort')}
            else:d['parameters'].append(dict(name=body['variable'],sort=body['sort']))
            body=body['body']
        d['body']=retained|dict(body=body)
    if mode=='instance':
        b=d['body'];assert b['kind']=='forall' and b['sort']==SEQ
        d['parameters'].append(dict(name=b['variable'],sort=b['sort']));d['body']=b['body']
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jopm'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jopmpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jopmpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jopmcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jopmcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'aa':lambda a,b:a<b,'jopmpoint':lambda:'case','jopmcapture':capture}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}
    value=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else value

@lru_cache(None)
def reconstruction_checks():
    cuts,m=numbers();c=cuts.make;cases=0
    new=(field(c,(1,-2,Q(15,2))),field(c,(4,Q(17,2),6)))
    readers=[function(['individual'],FS,lambda rec,f=f:f if rec=='answer' else field(c,(0,0,0))) for f in new]
    def extract(ans,e,h):return 'solution' if ans.items==('otheranswer','answer') and field_key(e,cuts)==(1,2,3) and field_key(h,cuts)==(4,5,6) else 'wrong'
    mapper=function([SEQ],'individual',lambda a:'solution');extractor=function([SEQ,FS,FS],'individual',extract)
    values=[c(5),c(3),*readers,extractor,mapper,Q(1)]
    ans=sequence('otheranswer','answer')
    assert run('ekwo',values+[ans,'answer'],m);cases+=1
    for i,wrong in [(1,c(-3)),(2,readers[1]),(3,readers[0]),(4,function([SEQ,FS,FS],'individual',lambda *xs:'wrong')),(5,function([SEQ],'individual',lambda a:'wrong'))]:
        bad=values.copy();bad[i]=wrong;assert not run('ekwo',bad+[ans,'answer'],m),i;cases+=1
    for a,rec in [(sequence('answer','otheranswer'),'answer'),(ans,'wrong')]:assert not run('ekwo',values+[a,rec],m);cases+=1
    # One explicit sequence instance, with the actual complete-answer predicate
    # and native position lookup. The unbounded sequence quantifier is retained
    # in production and refused below.
    qs=function(['individual'],dict(kind='question',parameters=['individual']),lambda p:question(['individual'],lambda a:a==('answer' if p=='fieldproblem' else 'otheranswer')))
    base=values+[sequence('target','fieldproblem'),qs]
    seen=[]
    def rebuilt(*xs):seen.append(xs[-1]);return xs[-1]=='answer' and xs[-2].items==ans.items
    assert run('ekwp',base+[ans],m|{'ekwo':rebuilt},'instance');assert seen;cases+=1
    assert not run('ekwp',base+[ans],m|{'ekwo':lambda *xs:False},'instance');cases+=1
    bad=base.copy();bad[6]=Q(0)
    assert not run('ekwp',bad+[ans],m|{'ekwo':rebuilt},'instance');cases+=1
    rejects(lambda:run('ekwp',base,m|{'ekwo':rebuilt}));cases+=1
    rejects(lambda:run('ekwo',values+[ans,'answer'],m|{'be':forbidden}),'Unknown optical-method');cases+=1
    return dict(cases=cases,both_inverse_fields_and_entire_ordered_answer_sequence_checked=True,all_answer_quantifier_not_finitely_sampled=True)

@lru_cache(None)
def witness_checks():
    cases=0
    for pivot,(variable,t) in enumerate(WITNESSES):
        for target in (('case','other','unavailable') if t=='d' else ('a','b','unavailable')):
            by={n:'case' if t=='d' else ('a' if i%2==0 else 'b') for i,(n,t) in enumerate(DETAIL)}
            by[variable]=target;row=tuple(by[n] for n,t in DETAIL)
            values=[by[n] for n,t in PLAN]+[by[n] for i,(n,t) in enumerate(WITNESSES) if i!=pivot]
            assert run('ekws',values,{'ekwr':lambda *xs,row=row:xs==row},f'slot:{pivot}',('a','b'))==(target!='unavailable'),variable;cases+=1
        rejects(lambda:run('ekws',values,{'ekwr':forbidden},f'slot:{pivot}',('a','b')),'Unknown optical-method');cases+=1
    rejects(lambda:run('ekws',['method','sourceproblem',sequence('target','fieldproblem'),function([SEQ],'individual',lambda a:'solution'),'case'],{'ekwr':lambda *xs:True}));cases+=1
    return dict(cases=cases,all_33_shared_witness_slots_distinguished=True,two_value_binding_diagnostics_not_a_physical_model=True)

@lru_cache(None)
def method_checks():
    cuts,m,_,by,new=method_setup();c=cuts.make;cases=0
    m['tc']=lambda:c(5)
    def key(x):
        if isinstance(x,(tuple,list)):return tuple(key(v) for v in x)
        if isinstance(x,SequenceValue):return tuple(key(v) for v in x.items)
        if isinstance(x,FunctionValue):
            try:return cuts.read(x)
            except ValueError:pass
            # Compare identity of issued fixture functions through the finite
            # evaluator's type-checking wrapper, not global function equality.
            while isinstance(x,FunctionValue):
                fn=x.implementation;code=getattr(fn,'__code__',None)
                if code is None:return fn
                closed=dict(zip(code.co_freevars,(cell.cell_contents for cell in (getattr(fn,'__closure__',None) or ()))))
                if 'raw' not in closed:return fn
                x=closed['raw']
        return x
    by|={'lightsource':'lightsource','wave':'wave','method':'method','sourceproblem':'sourceproblem','targets':sequence('target','fieldproblem'),'mapper':function([SEQ],'individual',lambda a:'solution'),'reference':'other','fieldproblem':'fieldproblem','slot':Q(1),'extractor':function([SEQ,FS,FS],'individual',lambda *xs:'solution')}
    native=question(['individual'],lambda a:a=='answer')
    captured={}
    def remember(name,fn=lambda *xs:True):
        def f(*xs):captured.setdefault(name,[]).append(xs);return fn(*xs)
        return f
    mm=m|{n:remember(n) for n in ('sca','ekwq','ekwi','ekwe','ekwp','eisvn')}
    mm|={'ekwf':remember('ekwf',lambda *xs:native),'eisvm':lambda p,ctx:native,'eisvl':remember('eisvl',lambda p,proc,body,frame,ctx,ref:(proc,body,ctx,ref)==(by['process'],by['body'],'case','other') and frame==('old' if p=='sourceproblem' else 'new'))}
    values=[by[n] for n,t in DETAIL]
    assert run('ekwr',values,mm);cases+=1
    assert key(captured['ekwq'][0])==key(tuple(by[n] for n,t in OPERATION))
    assert key(captured['ekwi'][0])==key(captured['ekwf'][0])==key(tuple(by[n] for n,t in METHOD))
    assert key(captured['eisvn'][0])==key(tuple(by[n] for n in ('method','sourceproblem','targets','slot','extractor','reference')))
    assert captured['ekwe'][0][0]=='fieldproblem' and captured['ekwe'][0][1]('target').function('answer')
    assert key(captured['ekwp'][0][:7])==key(tuple(by[n] for n,t in REBUILD)) and key(captured['ekwp'][0][7])==key(by['targets'])
    for n in ('sca','ekwq','ekwi','ekwe','ekwp','eisvn','eisvl'):
        assert not run('ekwr',values,mm|{n:lambda *xs:False}),n;cases+=1
        rejects(lambda:run('ekwr',values,mm|{n:forbidden}),'Unknown optical-method');cases+=1
    for fieldname,bad in [('targets',sequence('fieldproblem')),('slot',Q(0)),('slot',Q(-1)),('slot',Q(2)),('fieldproblem','target'),('oldframe','new'),('newframe','old'),('reference','case')]:
        changed=by|{fieldname:bad};assert not run('ekwr',[changed[n] for n,t in DETAIL],mm),fieldname;cases+=1
    for rejected in ('target','fieldproblem'):
        assert not run('ekwr',values,mm|{'eisvl':lambda p,*xs:p!=rejected});cases+=1
    # Centre operation preserves the radiation and both full chart conventions.
    seen=[]
    def chart(first,second,lu,tu,f,ctx):
        seen.append((first,second));sign=1 if (first,second)==('old','new') else -1
        out=f(point(c,(1,2,3,1)))
        return tuple(cuts.read(out(a)) for a in ('x','y','z','t'))==(Q(5,4)*(1-sign*3),Q(2),Q(3),Q(5,4)*(1-Q(sign*3,25))) and (lu,tu,ctx)==('lengthunit','timeunit','case')
    emitted=(by['lightsource'],by['process'],by['wave'],'old','lengthunit','timeunit',by['electricunit'],by['magneticunit'],by['electricfield'],by['magneticfield'],by['region'],'case')
    opm=m|{'eisru':lambda *xs:key(xs)==key(emitted),'ekv6':lambda *xs:key(xs)==key(tuple(by[n] for n,t in SETTING)),'eisqt':chart}
    assert run('ekwq',[by[n] for n,t in OPERATION],opm);assert set(seen)=={('old','new'),('new','old')};cases+=1
    for n in ('eisru','ekv6','eisqt'):
        assert not run('ekwq',[by[n] for n,t in OPERATION],opm|{n:lambda *xs:False});cases+=1
    # The native topic condition uses a general radiation/process attribution,
    # calibrated fields and influence, with moving/resting body history added
    # independently. No target-frame or answer witness occurs in this schema.
    by|={'oldlower':c(0),'oldupper':c(2)}
    calibration=(by['oldframe'],'lengthunit','timeunit','case',by['region'],*[by[n] for n in ('chargeunit','electricunit','magneticunit','forceunit')],c(1),c(Q(1,5)),by['electricfield'],by['magneticfield'])
    def calibrated(*xs):return key(xs)==key(calibration)
    topic=m|{'ejsn':calibrated,'eisru':lambda *xs:key(xs)==key(emitted),'eisvi':lambda *xs:key(xs)==key((by['body'],by['process'],'old',by['region'],'case'))}
    casevalues=[by[n] for n,t in CASE]
    assert run('ekwl',casevalues,topic);cases+=1
    for n in ('ejsn','eisru','eisvi'):
        assert not run('ekwl',casevalues,topic|{n:lambda *xs:False});cases+=1
        rejects(lambda:run('ekwl',casevalues,topic|{n:forbidden}),'Unknown optical-method');cases+=1
    for n,x in [('light',-5),('oldlower',2),('oldupper',0)]:
        bad=by|{n:c(x)};assert not run('ekwl',[bad[n] for n,t in CASE],topic);cases+=1
    expected=(by['body'],'old','case','lengthunit','timeunit',by['oldlower'],by['oldupper'],by['members'],by['oldx'],by['oldy'],by['oldz'])
    for root,motion in [('ekwm','eiag'),('ekwn','eiah')]:
        joined={'ekwl':lambda *xs:key(xs)==key(tuple(casevalues)),motion:lambda *xs:key(xs)==key(expected)}
        assert run(root,casevalues,joined);cases+=1
        for n in joined:assert not run(root,casevalues,joined|{n:lambda *xs:False});cases+=1
    return dict(cases=cases,same_setting_questions_and_all_target_roles_preserved=True,plural_series_and_distinct_physical_discourse_contexts=True,radiation_and_both_global_chart_directions_checked=True)

@lru_cache(None)
def scope_checks():
    from scripts.check_rod_methods import value
    cases=0;selected={'sourceproblem','fieldproblem'}
    def actual(p,ctx):return question(['individual'],lambda a:a==p and ctx=='case')
    def classify(p,q,topic,scope,ctx):return p in selected and q.function(p) and value(topic)=='ekwm' and (scope,ctx)==('scope','case')
    mm={'eisvm':actual,'eisvk':classify}
    chosen=run('ekwu',['case'],mm)
    for p in DOMAIN:assert chosen(p)==(p in selected);cases+=1
    # The question may have no answers; topic classification is still true.
    empty={'eisvm':lambda *xs:question(['individual'],lambda a:False),'eisvk':lambda p,*xs:p in selected}
    assert run('ekwu',['case'],empty)('sourceproblem');cases+=1
    for root,inner in [('ekwx','ekvs'),('ekwy','ekvq')]:
        calls=[]
        def solution(method,source,qs,targets,plans,ctx):
            calls.append(source)
            return method=='method' and ctx=='case' and qs(source).function(source) and targets('target') and not targets('sourceproblem')
        def classify_both(p,q,topic,scope,ctx):return (p in selected if value(topic)=='ekwm' else p=='target') and (scope,ctx)==('scope','case')
        model=mm|{'eisvk':classify_both,inner:solution}
        assert run(root,[],model);assert selected<=set(calls);cases+=1
        for missing in selected:
            assert not run(root,[],model|{inner:lambda method,p,*xs:p!=missing});cases+=1
        assert not run(root,[],model|{'eisvk':lambda *xs:False});cases+=1
        rejects(lambda:run(root,[],model|{inner:forbidden}),'Unknown optical-method');cases+=1
    return dict(cases=cases,all_topic_problems_not_only_solvable_cases=True,native_question_family_and_nonempty_universal_scope=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    rows={
      'ekww':{'eisvo':{('method','ekwq','scope','case')}},
      'ekwz':{'uh':{('first','author','ekwx','scope','case')},'eisvq':{('method','prioruse','ekti','paper','case')}},
      'ekw2':{'uh':{('second','author','ekww','scope','case')}},
      'ekw3':{'uh':{('third','author','ekwy','scope','case')},'eisvr':{('third','author','method','ekwq','ekwy','scope','case')},'eisra':{('third','author','paper','second','ekww','ekwy','scope','case')}},
      'ekw6':{'eir3':{('first','author','paper','ekw5','case')},'ue':{('previous','first','case')}},
    }
    for root,rs in rows.items():cases+=perturb(lambda model:run(root,[],model),{n:relation(r) for n,r in rs.items()},rs)
    allrows={n:set().union(*(rs.get(n,set()) for root,rs in rows.items() if root in ('ekwz','ekw2','ekw3'))) for n in ('uh','eisvq','eisvr','eisra')}
    allrows['ue']={('first','second','case'),('second','third','case')}
    cases+=perturb(lambda model:run('ekw4',[],model),{n:relation(r) for n,r in allrows.items()},allrows)
    return dict(cases=cases,three_sentences_prior_reference_essential_operation_and_instrumental_result_checked=True,quoted_physical_claims_not_assumed_true=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==407 and new.document['statements'][:406]==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[404,405])==selection_binding(old,[404,405])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    deps=set(selection_binding(new,[INDEX])['dependencies']);assert set(MEANINGS)|{'ekvt','ekvr','ekwi','ekv6','eisru','eisqt','s6k','s6l'}<=deps
    assert not {'ekbw','ekbx','ekby','ekbz'}&deps
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(READING))==build_reading()
    return dict(new_definitions=len(MEANINGS),new_general_relations=7,new_reference_individuals=4,all_406_previous_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('reconstruction',reconstruction_checks),('witnesses',witness_checks),('method',method_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_body_rest_field_method','compose_field_answer_records','compose_relativity_conjecture','compose_two_postulates','check_field_answer_records','check_body_rest_field_method','check_material_relative_frame','check_problem_series_reduction','check_clock_site_time','check_rod_methods','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(READING))['source_sha256'])|{READING,DOC,*DEPENDENCIES,'scripts/compose_optical_problem_method.py','scripts/read_optical_problem_method.py','scripts/check_optical_problem_method.py','tests/test_optical_problem_method.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='whole_optical_method_claim_connected_and_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
