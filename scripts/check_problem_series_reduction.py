"""Native ordered questions and isolated quantifier/argument diagnostics."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes,selection_binding
from noema.script import transcribe
from scripts.compose_problem_series_reduction import *

DOC='docs/problem-series-reduction-v1.md'
DEPENDENCIES=('reports/pressure-leading-approximation-v1.json',)
DOMAIN=('source','p','q','r','x','y','z','solution','wrong','method','other','a','b')
SEQ=dict(kind='sequence',element='individual')
QUESTION=dict(kind='question',parameters=['individual'])
MAP=dict(kind='function',parameters=[SEQ],result='individual')

def forbidden(*xs):raise ValueError('Unknown problem-series input')
def sequence(*items):return SequenceValue(tuple(items),'"individual"')
def function(params,result,fn):return FunctionValue(tuple(params),result,fn)
def questions(rows):
    # Complete explicit finite interpretation, including non-problem objects.
    table={p:frozenset(rows.get(p,())) for p in DOMAIN}
    return function(['individual'],QUESTION,lambda p:QuestionValue(function(['individual'],'truth',lambda a:a in table[p])))

@lru_cache(None)
def core():return parse(read(CORE))

def collapse(node):
    if isinstance(node,list):return [collapse(x) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind') in ('sequence','function','question'):return 'individual'
    return {k:collapse(v) for k,v in node.items()}

@lru_cache(None)
def fixture(root,cuts=(),mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['name'] in set(cuts)|{'aa'} and d['kind']!='primitive':
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='binding':doc=collapse(doc)
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode=='instance':
        # Only lift the actual all-answer binder; this is one instance, not
        # an interpretation of the unbounded sequence quantifier.
        holder=d['body']['arguments'][1]
        assert holder['kind']=='forall' and holder['sort']==SEQ
        d['parameters'].append(dict(name=holder['variable'],sort=holder['sort']))
        d['body']['arguments'][1]=holder['body']
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpsr'+number_word(i);slots.append(n)
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jpsrcapture',parameters=[d['result']],result='truth'))
        expr=dict(kind='call',symbol='jpsrcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,values,model=None,cuts=(),mode='native',domain=DOMAIN):
    doc,slots=fixture(root,tuple(cuts),mode);assert len(values)==len(slots),(root,len(values),len(slots))
    captured=[]
    def capture(x):captured.append(x);return True
    mm={'aa':lambda x,y:x<y,'jpsrcapture':capture}|(model or {})|{n:lambda x=x:x for n,x in zip(slots,values)}
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def rejects(call,phrase):
    try:call()
    except ValueError as e:assert phrase in str(e),str(e)
    else:raise AssertionError('Expected rejection: '+phrase)

@lru_cache(None)
def sequence_checks():
    cases=0;qs=questions({'p':{'x'},'q':{'y'},'r':{'z'},'source':{'solution'}})
    classified=function(['individual'],'truth',lambda p:p in ('p','q','r'))
    for items in ((),('p',),('p','q'),('p','q','p'),('r','p','q','p','r')):
        xs=sequence(*items);indices=run('ekvg',[xs])
        assert indices.items==tuple(Fraction(i) for i in range(len(items))) and indices.element_type=='"number"';cases+=1
        assert run('ekvh',[xs,classified])==bool(items);cases+=1
        ys=tuple({'p':'x','q':'y','r':'z'}[p] for p in items)
        assert run('ekvi',[xs,sequence(*ys),qs])==bool(items);cases+=1
        for i in range(len(items)):
            wrong=list(ys);wrong[i]='wrong';assert not run('ekvi',[xs,sequence(*wrong),qs]);cases+=1
        assert not run('ekvi',[xs,sequence(*ys,'x'),qs]);cases+=1
        if ys:assert not run('ekvi',[xs,sequence(*ys[:-1]),qs]);cases+=1
    assert not run('ekvi',[sequence('p','q'),sequence('y','x'),qs]);cases+=1
    assert not run('ekvh',[sequence('p','wrong'),classified]);cases+=1
    for i in range(3):
        selected={'p','q','r'}-{{0:'p',1:'q',2:'r'}[i]}
        assert not run('ekvh',[sequence('p','q','r'),function(['individual'],'truth',lambda p:p in selected)]);cases+=1
    missing=questions({'p':{'x'},'q':set(),'source':{'solution'}})
    assert not run('ekvi',[sequence('p','q'),sequence('x','y'),missing]);cases+=1
    rejects(lambda:run('ekvh',[sequence('p'),function(['individual'],'truth',forbidden)]),'Unknown problem-series')
    rejects(lambda:run('ekvi',[sequence('p'),sequence('x'),function(['individual'],QUESTION,forbidden)]),'Unknown problem-series');cases+=2
    return dict(cases=cases,arbitrary_finite_length_order_repetition_and_every_position=True,native_questions_and_answers=True,unknown_inputs_rejected=True)

@lru_cache(None)
def reconstruction_checks():
    cases=0;qs=questions({'p':{'x'},'q':{'y'},'source':{'solution'}});targets=sequence('p','q')
    mapper=function([SEQ],'individual',lambda xs:'solution' if xs.items==('x','y') else 'wrong')
    base=['source',targets,qs,mapper]
    assert run('ekvj',base+[sequence('x','y')]);cases+=1
    for xs in (sequence('y','x'),sequence('x'),sequence('x','y','x')):
        assert not run('ekvj',base+[xs]);cases+=1
    assert not run('ekvj',['other',*base[1:],sequence('x','y')]);cases+=1
    assert not run('ekvj',[*base[:2],questions({}),mapper,sequence('x','y')]);cases+=1
    bad=function([SEQ],'individual',lambda xs:'wrong')
    assert not run('ekvj',[*base[:3],bad,sequence('x','y')]);cases+=1
    for xs in (sequence('x','y'),sequence('wrong','y'),sequence('x'),sequence()):
        assert run('ekvk',base+[xs],mode='instance');cases+=1
        assert run('ekvk',[*base[:3],bad,xs],mode='instance')==(xs.items!=('x','y'));cases+=1
    assert not run('ekvk',['source',sequence(),qs,mapper,sequence()],mode='instance');cases+=1
    assert run('ekvn',['source',qs]) and not run('ekvn',['other',qs]);cases+=2
    for root,vs in [('ekvk',base),('ekvl',[targets,qs])]:
        rejects(lambda:run(root,vs),'unbounded sequence domain');cases+=1
    # Even a false antecedent does not supply unknown reconstruction semantics.
    rejects(lambda:run('ekvk',[*base[:3],function([SEQ],'individual',forbidden),sequence('wrong')],mode='instance'),'Unknown problem-series');cases+=1
    rejects(lambda:run('ekvj',[*base[:3],function([SEQ],'individual',forbidden),sequence('x','y')]),'Unknown problem-series');cases+=1
    return dict(cases=cases,same_ordered_answer_tuple_reconstructed=True,conditional_correctness_distinct_from_target_solvability=True,native_unbounded_sequence_quantification_refused=True)

def exact(row):return lambda *xs:xs==row

@lru_cache(None)
def binding_checks():
    cases=0
    # Complex sorts are replaced only in isolated binding diagnostics. All
    # native question and finite-sequence operations are checked separately.
    for witness in ('a','b','unavailable'):
        row=('a',witness,'b')
        assert run('ekvl',['a','b'],{'ekvi':exact(row)},('ekvi',),'binding',('a','b'))==(witness!='unavailable');cases+=1
        for i in (0,2):
            changed=list(row);changed[i]='b' if row[i]=='a' else 'a'
            assert not run('ekvl',['a','b'],{'ekvi':exact(tuple(changed))},('ekvi',),'binding',('a','b'));cases+=1
    # Shared roles at each composed boundary, each side independently needed.
    for root,fields,bounds in [('ekvm',REDUCTION,{'ekvk':REDUCTION,'ekvl':[('targets',SEQUENCE),('questions',QUESTIONS)]}),('ekvo',CLASSIFIED,{'ekvh':[('targets',SEQUENCE),('targetclass',CLASS)],'ekvk':REDUCTION})]:
        by={n:('a' if i%2==0 else 'b') for i,(n,t) in enumerate(fields)}
        rows={n:tuple(by[k] for k,t in fs) for n,fs in bounds.items()};mm={n:exact(r) for n,r in rows.items()};vs=[by[n] for n,t in fields]
        assert run(root,vs,mm,tuple(bounds),'binding',('a','b'));cases+=1
        for n,row in rows.items():
            for i in range(len(row)):
                bad=tuple(('b' if x=='a' else 'a') if j==i else x for j,x in enumerate(row))
                assert not run(root,vs,mm|{n:exact(bad)},tuple(bounds),'binding',('a','b'));cases+=1
            rejects(lambda:run(root,vs,mm|{n:forbidden},tuple(bounds),'binding',('a','b')),'Unknown problem-series');cases+=1
    for root in ('ekvq','ekvs'):
        by={n:('case' if t=='d' else ('a' if i%2==0 else 'b')) for i,(n,t) in enumerate(PROBLEM)}
        vs=[by[n] for n,t in PROBLEM];cuts=('ekvp','ekvl') if root=='ekvs' else ('ekvp',)
        for targets,mapper in product(('a','b','unavailable'),repeat=2):
            row=tuple((by|dict(targets=targets,mapper=mapper))[n] for n,t in PLAN)
            mm={'ekvp':exact(row),'ekvl':exact((targets,by['questions']))}
            assert run(root,vs,mm,cuts,'binding',('a','b'))==('unavailable' not in (targets,mapper));cases+=1
            if 'unavailable' in (targets,mapper):continue
            for i,(n,t) in enumerate(PLAN):
                if n in ('targets','mapper'):continue
                bad=tuple(('other' if t=='d' else ('b' if x=='a' else 'a')) if j==i else x for j,x in enumerate(row))
                assert not run(root,vs,mm|{'ekvp':exact(bad)},cuts,'binding',('a','b'));cases+=1
            if root=='ekvs':
                opposite='b' if targets=='a' else 'a'
                assert not run(root,vs,mm|{'ekvl':exact((opposite,by['questions']))},cuts,'binding',('a','b'));cases+=1
                opposite='b' if by['questions']=='a' else 'a'
                assert not run(root,vs,mm|{'ekvl':exact((targets,opposite))},cuts,'binding',('a','b'));cases+=1
        rejects(lambda:run(root,vs,{'ekvp':forbidden,'ekvl':lambda *xs:True},cuts,'binding',('a','b')),'Unknown problem-series');cases+=1
    return dict(cases=cases,all_shared_roles_and_existential_witnesses_checked=True,plan_and_solution_require_same_target_sequence=True,two_individual_binding_domain_only=True)

@lru_cache(None)
def method_checks():
    cases=0;qs=questions({'source':{'solution'},'p':{'x'}});targets=sequence('p')
    mapper=function([SEQ],'individual',lambda xs:'solution');targetclass=function(['individual'],'truth',lambda p:p=='p')
    # Fingerprints are only finite diagnostic probes, not extensional equality.
    def fp(x):
        if isinstance(x,SequenceValue):return x.items
        if isinstance(x,FunctionValue):
            if x.result=='individual':return ('mapper',x(sequence('x')))
            if len(x.parameters)==5:return ('plans',tuple(x(m,'source',targets,mapper,c) for m in ('method','other') for c in ('case','other')))
            if x.result=='truth':return ('class',tuple(x(p) for p in ('p','q','source')))
            return ('questions',tuple(x(p).function(a) for p in ('p','source') for a in ('x','solution')))
        return x
    expected=tuple(map(fp,['source',targets,qs,mapper,targetclass]))
    expected_plan=tuple(map(fp,['method','source',targets,mapper,'case']))
    plans=function(['individual','individual',SEQ,MAP,'situation'],'truth',lambda *xs:tuple(map(fp,xs))==expected_plan)
    vs=['method','source',targets,qs,mapper,targetclass,plans,'case'];mm={'ekvo':lambda *xs:tuple(map(fp,xs))==expected}
    assert run('ekvp',vs,mm,('ekvo',));cases+=1
    replacements=['other','other',sequence('q'),questions({}),function([SEQ],'individual',lambda xs:'wrong'),function(['individual'],'truth',lambda p:False),function(['individual','individual',SEQ,MAP,'situation'],'truth',lambda *xs:False),'other']
    for i,x in enumerate(replacements):
        bad=vs.copy();bad[i]=x;assert not run('ekvp',bad,mm,('ekvo',));cases+=1
    rejects(lambda:run('ekvp',vs,{'ekvo':forbidden},('ekvo',)),'Unknown problem-series');cases+=1
    for root,inner in [('ekvr','ekvq'),('ekvt','ekvs')]:
        for selected in (set(),{'p'},{'p','q'},{'p','q','r'}):
            sc=function(['individual'],'truth',lambda x:x in selected)
            allvalues=['method',qs,targetclass,plans,'case',sc]
            fixed=['method',qs,targetclass,plans,'case']
            def gate(*xs):return xs[0]=='method' and tuple(map(fp,xs[2:]))==tuple(map(fp,fixed[1:]))
            assert run(root,allvalues,{inner:gate},(inner,))==bool(selected);cases+=1
            for p in selected:
                assert not run(root,allvalues,{inner:lambda *xs,p=p:gate(*xs) and xs[1]!=p},(inner,));cases+=1
            if selected:
                for i in (0,2,3,4,5):
                    def wrong(*xs,i=i):
                        expected=['method',None,qs,targetclass,plans,'case'][i]
                        return fp(xs[i])!=fp(expected)
                    assert not run(root,allvalues,{inner:wrong},(inner,));cases+=1
        rejects(lambda:run(root,allvalues,{inner:forbidden},(inner,)),'Unknown problem-series');cases+=1
    for antecedent in (False,True):
        for answers in ({'solution'},set()):
            qsource=questions({'source':answers})
            assert run('ekvu',['source',targets,qsource,mapper],{'ekvm':lambda *xs:antecedent},('ekvm',))==(not antecedent or bool(answers));cases+=1
    # Quantified method witnesses must still reject native unbounded domains.
    for root in ('ekvq','ekvs'):
        rejects(lambda:run(root,['method','source',qs,targetclass,plans,'case'],{'ekvp':lambda *xs:True,'ekvl':lambda *xs:True},('ekvp','ekvl')),'unbounded sequence domain');cases+=1
    return dict(cases=cases,method_source_target_mapper_context_bound=True,nonempty_entire_source_scope_required=True,reduction_existence_and_solvability_distinct=True,logical_consequence_checked_separately=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==406 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[404,405])==selection_binding(old,[404,405])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/pressure-leading-approximation-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert not {'ekbw','ekbx','ekby','ekbz'}&{d['name'] for d in core()['declarations']}
    for style in ('compact','full'):
        text=format_graph(core(),style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,all_406_previous_statements_and_meanings_preserved=True,no_additional_source_unit_judged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('sequences',sequence_checks),('reconstruction',reconstruction_checks),('bindings',binding_checks),('methods',method_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'scripts/compose_problem_series_reduction.py','scripts/check_problem_series_reduction.py','tests/test_problem_series_reduction.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/audit_opening_scope.py'}
    return dict(status='ordered_question_reduction_dependency_group_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
