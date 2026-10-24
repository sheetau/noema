"""Check typed record contents, complete native answers and ordered subproblem attachment."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_body_rest_field_method import numbers,scalar_oracle,fingerprint,CONSTANTS,point
from scripts.check_material_relative_frame import NUM,RS
from scripts.compose_field_answer_records import *

DOC='docs/field-answer-records-v1.md'
DEPENDENCIES=('reports/body-rest-field-method-v1.json','reports/problem-series-reduction-v1.json','reports/comoving-wording-v1.json','reports/vacuum-equation-assumption-v1.json')
DOMAIN=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in META if t=='a'],*[n for n,t in SETTING if t=='a'],'old','new','answer','wrong','problem','otherproblem','otheranswer','other','a','b']))
SCALAR=dict(kind='function',parameters=[RS]*4,result=RS)
FS=dict(kind='function',parameters=['individual'],result=SCALAR)
QS=dict(kind='question',parameters=[FS,FS])
BOUNDS={'ekwc':{'ejs3'},'ekwd':{'ekwc','ekwa'},'ekwf':{'ekv5'},'ekwh':{'ekv6','ekwc','ekwf'},'ekwi':{'ekwd','ekwh','ekv5'},'ekwj':{'ekwe','ekwi','ekwf','ekwg'},'ekwk':{'ekwj','ekwg'}}

def forbidden(*xs):raise ValueError('Unknown field-answer-record input')
def function(parameters,result,fn):return FunctionValue(tuple(parameters),result,fn)
def question(parameters,fn):return QuestionValue(function(parameters,'truth',fn))
def sequence(*xs):return SequenceValue(tuple(xs),'"individual"')
def rejects(fn,text):
    try:fn()
    except ValueError as e:assert text in str(e),str(e)
    else:raise AssertionError('Expected rejection: '+text)

@lru_cache(None)
def core():return parse(read(CORE))

def field_to_individual(node):
    if node==FS:return 'individual'
    if isinstance(node,list):return [field_to_individual(x) for x in node]
    if isinstance(node,dict):return {k:field_to_individual(v) for k,v in node.items()}
    return node

@lru_cache(None)
def fixture(root,mode='native'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    cuts=NUM|{'bg','be','sjd','sje','soy','szi'}|BOUNDS.get(root,set())
    if mode=='full_region':cuts.discard('ejs3')
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in cuts:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    if mode=='binding':doc=field_to_individual(doc)
    d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jfar'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jfarcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jfarcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(root,mode);assert len(values)==len(slots),(root,len(values),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|model|{n:lambda x=x:x for (n,s),x in zip(slots,values)}|{'jfarcapture':capture}
    result=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

def field(c,values):return function(['individual'],SCALAR,lambda a:function([RS]*4,RS,lambda *xs:c(values[('x','y','z').index(a)] if a in ('x','y','z') else 0)))
def field_key(f,cuts):return tuple(cuts.read(f(a)(*[cuts.make(0)]*4)) for a in ('x','y','z'))

def setup():
    cuts,m=numbers();c=cuts.make
    ef,hf=field(c,(1,2,3)),field(c,(4,5,6));bad=field(c,(7,8,9))
    readers=[function(['individual'],FS,lambda rec,f=f:f if rec=='answer' else bad) for f in (ef,hf)]
    encoder=function([FS,FS],'individual',lambda e,h:'answer' if field_key(e,cuts)==(1,2,3) and field_key(h,cuts)==(4,5,6) else 'wrong')
    region=function([RS]*4,'truth',lambda *xs:True)
    meta=[n if t=='a' else 'case' if t=='d' else region for n,t in META]
    native=question([FS,FS],lambda e,h:field_key(e,cuts)==(1,2,3) and field_key(h,cuts)==(4,5,6))
    vals=meta+readers+[encoder,native]
    def payload(rec,*xs):
        prefix=xs[:-2]
        return rec=='answer' and prefix[:9]==tuple(meta[:9]) and prefix[-1]=='case' and prefix[9](*[c(0)]*4) and field_key(xs[-2],cuts)==(1,2,3) and field_key(xs[-1],cuts)==(4,5,6)
    return cuts,m|{'eisvj':payload},vals,(ef,hf,bad)

@lru_cache(None)
def record_checks():
    cuts,m,values,(ef,hf,bad)=setup();cases=0;c=cuts.make
    assert run('ekwa',values+['answer'],m);cases+=1
    assert not run('ekwa',values+['wrong'],m);cases+=1
    lifted=run('ekwb',values,m);assert lifted.function('answer') and not lifted.function('wrong');cases+=2
    for i,(n,t) in enumerate(TASK):
        wrong=values.copy()
        if t in ('a','d'):wrong[i]='other'
        elif n=='region':wrong[i]=function([RS]*4,'truth',lambda *xs:False)
        elif n in ('electricreader','magneticreader'):wrong[i]=function(['individual'],FS,lambda rec:bad)
        elif n=='question':wrong[i]=question([FS,FS],lambda *xs:False)
        else:continue # encoder is intentionally unused while reading a record.
        assert not run('ekwa',wrong+['answer'],m),n;cases+=1
    rejects(lambda:run('ekwa',values+['answer'],m|{'eisvj':forbidden}),'Unknown field-answer-record');cases+=1
    equal=lambda a,b,region:field_key(a,cuts)==field_key(b,cuts)
    mm=m|{'ejs3':equal};packvals=values[:-1]+[ef,hf]
    assert run('ekwc',packvals,mm);cases+=1
    for changed in ([hf,ef],[bad,hf],[ef,bad]):assert not run('ekwc',values[:-1]+changed,mm);cases+=1
    wrong=values[:-1];wrong[-1]=function([FS,FS],'individual',lambda *xs:'wrong')
    assert not run('ekwc',wrong+[ef,hf],mm);cases+=1
    rejects(lambda:run('ekwc',packvals,mm|{'ejs3':forbidden}),'Unknown field-answer-record');cases+=1
    rejects(lambda:run('ekwc',packvals,m,'full_region'),'rational number domain');cases+=1
    return dict(cases=cases,actual_typed_payload_metadata_and_native_question_checked=True,regional_pair_equality_not_function_identity=True,unknown_payload_and_full_region_refused=True)

@lru_cache(None)
def completeness_checks():
    cuts,m,values,_=setup();cases=0
    rejects(lambda:run('ekwd',values,m|{'ekwc':lambda *xs:True,'ekwa':lambda *xs:True}),'rational number domain');cases+=1
    slots=fixture('ekwd','binding')[1]
    # Only FIELD is retagged; the two-answer question and its parameter order
    # remain native, with independent a/b witnesses for both bound fields.
    vals=[]
    for (n,t),(_,sort) in zip(TASK,slots):
        if t=='a':vals.append('a')
        elif t=='d':vals.append('case')
        elif n=='question':vals.append(None)
        elif n=='region':vals.append(function([RS]*4,'truth',lambda *xs:True))
        elif n=='encoder':vals.append(function(['individual','individual'],'individual',lambda e,h:'a' if e==h else 'b'))
        else:vals.append(function(['individual'],'individual',lambda rec:'a'))
    for selected in product(('a','b'),repeat=2):
        vals[-1]=question(['individual','individual'],lambda e,h:(e,h)==selected)
        expected='a' if selected[0]==selected[1] else 'b'
        mm={'ekwc':lambda *xs:xs[-2:]==selected,'ekwa':lambda *xs:xs[-1]==expected}
        assert run('ekwd',vals,mm,'binding',('a','b'));cases+=1
        for name in ('ekwc','ekwa'):
            assert not run('ekwd',vals,mm|{name:lambda *xs:False},'binding',('a','b'));cases+=1
            rejects(lambda:run('ekwd',vals,mm|{name:forbidden},'binding',('a','b')),'Unknown field-answer-record');cases+=1
        for i in (0,1):
            wrong=tuple(('b' if x=='a' else 'a') if j==i else x for j,x in enumerate(selected))
            assert not run('ekwd',vals,mm|{'ekwc':lambda *xs:xs[-2:]==wrong},'binding',('a','b'));cases+=1
    vals[-1]=question(['individual','individual'],lambda *xs:False)
    assert run('ekwd',vals,{'ekwc':lambda *xs:False,'ekwa':lambda *xs:False},'binding',('a','b'));cases+=1
    # Both selected pairs must succeed; one represented answer is insufficient.
    vals[-1]=question(['individual','individual'],lambda e,h:e==h)
    assert not run('ekwd',vals,{'ekwc':lambda *xs:xs[-2:]==('a','a'),'ekwa':lambda *xs:True},'binding',('a','b'));cases+=1
    return dict(cases=cases,both_field_quantifiers_and_all_native_answers_preserved=True,empty_answer_set_not_confused_with_solution_existence=True,complete_encoding_requires_question_preservation=True)

def method_setup(root='ekwh'):
    cuts,m=numbers();c=cuts.make;slots=fixture(root)[1];by={}
    for i,((n,t),(_,sort)) in enumerate(zip(METHOD,slots)):
        by[n]=n if t=='a' else 'case' if t=='d' else scalar_oracle(sort,i+1,c)
    old=(field(c,(1,2,3)),field(c,(4,5,6)));new=(field(c,(1,-2,Q(15,2))),field(c,(4,Q(17,2),6)))
    by|={'oldframe':'old','newframe':'new','light':c(5),'speed':c(3),'electricfield':old[0],'magneticfield':old[1],'region':function([RS]*4,'truth',lambda *xs:True),'encoder':function([FS,FS],'individual',lambda e,h:'answer' if (field_key(e,cuts),field_key(h,cuts))==tuple(field_key(x,cuts) for x in new) else 'wrong')}
    for n,f in zip(('electricreader','magneticreader'),new):by[n]=function(['individual'],FS,lambda rec,f=f:f)
    return cuts,m,[by[n] for n,t in METHOD],by,new

@lru_cache(None)
def method_checks():
    cuts,m,values,by,new=method_setup();c,r=cuts.make,cuts.read;cases=0
    assert run('ekwg',values,m)=='answer';cases+=1
    native=question([FS,FS],lambda e,h:tuple(field_key(x,cuts) for x in (e,h))==tuple(field_key(x,cuts) for x in new))
    actual=[by[n] for n,t in SETTING];sorts=next(d for d in fixture('ekwf')[0]['declarations'] if d['name']=='ekv5')['parameters']
    settingkey=tuple(fingerprint(x,s,cuts) for x,s in zip(actual,sorts))
    def same_setting(xs):return tuple(fingerprint(x,s,cuts) for x,s in zip(xs,sorts))==settingkey
    def qfactory(*xs):return native if same_setting(xs) else question([FS,FS],lambda *xs:False)
    def payload(rec,*xs):
        prefix=xs[:-2]
        return rec=='answer' and prefix[:9]==tuple([by['process'],by['body'],'new','lengthunit','timeunit',*[by[n] for n in ('chargeunit','electricunit','magneticunit','forceunit')]]) and prefix[-1]=='case' and prefix[9](*[c(0)]*4) and tuple(field_key(x,cuts) for x in xs[-2:])==tuple(field_key(x,cuts) for x in new)
    lifted=run('ekwf',values,m|{'ekv5':qfactory,'eisvj':payload});assert lifted.function('answer');cases+=1
    for i,(n,t) in enumerate(METHOD):
        if n in ('electricreader','magneticreader','encoder'):continue
        changed=values.copy();sort=fixture('ekwf')[1][i][1];changed[i]='other' if t in ('a','d') else scalar_oracle(sort,101+i,c)
        # speed/light must stay inside the explicit numeric oracle's domain.
        if n in ('speed','light'):continue
        q=run('ekwf',changed,m|{'ekv5':qfactory,'eisvj':payload});assert not q.function('answer'),n;cases+=1
    def charts(first,second,length,time,mapping,ctx):
        if (length,time,ctx)!=('lengthunit','timeunit','case'):return False
        sign=1 if (first,second)==('old','new') else -1 if (first,second)==('new','old') else 0
        if not sign:return False
        p=mapping(point(c,(1,2,3,1)));expected=(Q(5,4)*(1-sign*3),Q(2),Q(3),Q(5,4)*(1-Q(sign*3,25)))
        return tuple(r(p(a)) for a in ('x','y','z','t'))==expected
    def packed(*xs):return tuple(field_key(x,cuts) for x in xs[-2:])==tuple(field_key(x,cuts) for x in new)
    mm=m|{'eisqt':charts,'ekv6':lambda *xs:same_setting(xs),'ekwc':packed,'ekwf':lambda *xs:question(['individual'],lambda rec:rec=='answer')}
    assert run('ekwh',values,mm);cases+=1
    for n in ('eisqt','ekv6','ekwc'):
        assert not run('ekwh',values,mm|{n:lambda *xs:False});cases+=1
        rejects(lambda:run('ekwh',values,mm|{n:forbidden}),'Unknown field-answer-record');cases+=1
    for pair in (('old','new'),('new','old')):
        assert not run('ekwh',values,mm|{'eisqt':lambda *xs:xs[:2]!=pair and charts(*xs)});cases+=1
    # The all-answer contract and the actual construction must share the
    # entire setting, the readers and the same encoder at their join.
    def codec(xs):
        return tuple(field_key(reader('answer'),cuts) for reader in xs[:2])==tuple(field_key(f,cuts) for f in new) and xs[2](*new)=='answer'
    def complete(*xs):
        return payload('answer',*xs[:len(META)],*new) and codec(xs[len(META):len(META)+3]) and xs[-1].function(*new)
    def construction(*xs):return same_setting(xs[:len(SETTING)]) and codec(xs[len(SETTING):])
    joined=m|{'ekv5':qfactory,'ekwd':complete,'ekwh':construction}
    assert run('ekwi',values,joined);cases+=1
    for name in ('ekwd','ekwh'):
        assert not run('ekwi',values,joined|{name:lambda *xs:False});cases+=1
        rejects(lambda:run('ekwi',values,joined|{name:forbidden}),'Unknown field-answer-record');cases+=1
    return dict(cases=cases,same_setting_and_metadata_reach_actual_record_question=True,actual_mixed_fields_encoded=True,both_global_coordinate_conventions_bound=True)

@lru_cache(None)
def family_checks():
    cases=0;recordq=question(['individual'],lambda x:x=='answer')
    def family(p):return recordq if p=='problem' else question(['individual'],lambda x:x=='otheranswer')
    qs=function(['individual'],dict(kind='question',parameters=['individual']),family)
    assert run('ekwe',['problem',qs,recordq],{});cases+=1
    assert not run('ekwe',['otherproblem',qs,recordq],{});cases+=1
    assert not run('ekwe',['problem',qs,question(['individual'],lambda x:x in ('answer','wrong'))],{});cases+=1
    cuts,m,values,by,new=method_setup('ekwj')
    mm=m|{'ekwe':lambda *xs:xs[0]=='problem','ekwi':lambda *xs:True,'ekwf':lambda *xs:recordq,'ekwg':lambda *xs:'answer'}
    assert run('ekwj',values+['problem',qs],mm);cases+=1
    for name in ('ekwe','ekwi'):
        assert not run('ekwj',values+['problem',qs],mm|{name:lambda *xs:False});cases+=1
        rejects(lambda:run('ekwj',values+['problem',qs],mm|{name:forbidden}),'Unknown field-answer-record');cases+=1
    assert not run('ekwj',values+['otherproblem',qs],mm);cases+=1
    # Full native ekvi visits every position, including the other question.
    mm=m|{'ekwj':lambda *xs:True,'ekwg':lambda *xs:'answer'}
    for ts,ans,slot in [(('problem',),('answer',),0),(('otherproblem','problem'),('otheranswer','answer'),1),(('problem','otherproblem','problem'),('answer','otheranswer','answer'),2)]:
        base=values+['problem',qs,sequence(*ts),sequence(*ans),Q(slot)]
        assert run('ekwk',base,mm);cases+=1
        for i in range(len(ans)):
            changed=list(ans);changed[i]='wrong';bad=base.copy();bad[-2]=sequence(*changed)
            assert not run('ekwk',bad,mm);cases+=1
        for wrong in (Q(-1),Q(len(ts)),Q(1,2)):
            bad=base.copy();bad[-1]=wrong;assert not run('ekwk',bad,mm);cases+=1
        bad=base.copy();bad[-2]=sequence(*ans,'answer');assert not run('ekwk',bad,mm);cases+=1
    return dict(cases=cases,one_subproblem_attached_without_overwriting_other_questions=True,actual_record_at_same_ordered_slot_and_entire_series_checked=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==406 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[404,405])==selection_binding(old,[404,405])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/body-rest-field-method-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert not {'ekbw','ekbx','ekby','ekbz'}&{d['name'] for d in core()['declarations']}
    for style in ('compact','full'):
        text=format_graph(core(),style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==core()
    return dict(new_definitions=len(MEANINGS),new_general_relations=len(PRIMITIVES),all_406_previous_statements_and_meanings_preserved=True,no_additional_source_unit_judged=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('records',record_checks),('completeness',completeness_checks),('method',method_checks),('family',family_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_body_rest_field_method','compose_field_equations','check_body_rest_field_method','check_material_relative_frame','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,*DEPENDENCIES,'scripts/compose_field_answer_records.py','scripts/check_field_answer_records.py','tests/test_field_answer_records.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='typed_field_answers_attached_to_ordered_problem_series',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
