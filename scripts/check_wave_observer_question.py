"""Diagnose whole-interval rest, observation scope and field-pair questions."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_clock_site_time import unknowns,forbidden
from scripts.check_conductor_cases import sentinel,same_value
from scripts.check_moving_trip_geometry import norm_factory
from scripts.check_material_relative_frame import NUM,RS
from scripts.check_distant_wave_source import numbers
from scripts.check_unipolar_machine import finite_reals
from scripts.compose_wave_observer_question import ROOT,read,FULL,CORE,BASIS,ANNOTATIONS,PARENT_BASIS,MEANINGS,OBSERVER,TRACE,LOCATION,INVESTIGATION,QUESTION,ANSWERS,CALIBRATION,build

DOC='docs/wave-observer-question-v1.md';SOURCE='data/einstein-wave-observer-question-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
DEPENDENCIES=('reports/wave-display-v1.json','reports/observer-contrast-v1.json','reports/vacuum-field-domain-v1.json','reports/field-transformation-application-v1.json')
DOMAIN=tuple(dict.fromkeys([n for n,t in QUESTION if t=='a']+['a','b','body','other']))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'bg','lg','sjd','szi'}
    if name=='ekbu' and mode!='full_history':bounds.add('se')
    if name in ('ekbw','ekbx','ekby','ekbz'):bounds.add('ekbu')
    if name=='ekbx':bounds.add('ekbw')
    if name in ('ekby','ekbz'):bounds|={'ekbx','ejsn'}
    if mode=='finite':bounds.add('ekbv')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    if mode=='finite':doc=finite_reals(doc)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jwoq'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n,s in slots])
    if isinstance(d['result'],dict):
        doc['declarations'].append(dict(kind='primitive',name='jwoqcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jwoqcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,values,model,mode='native',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(values)==len(slots)
    mm=model|{n:lambda value=value:value for (n,s),value in zip(slots,values)};captured=[]
    def capture(value):captured.append(value);return True
    mm['jwoqcapture']=capture
    answer=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else answer

@lru_cache(None)
def rest_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;norm=norm_factory(cuts,(0,1,2));cases=0
    base=['observer','frame','case','lengthunit','timeunit',c(0),c(2)]
    def traces(which):
        return [FunctionValue((RS,),RS,lambda t,i=i:c(i+1+(r(t) if which=='drift' and i==0 else r(t)*(2-r(t)) if which=='return' and i==2 else 0))) for i in range(3)]
    for which in ('rest','drift','return'):
        values=base+traces(which);expected=norm(values)
        model=m|{'xb':lambda x:x=='observer','x4':lambda *xs:xs==('observer','frame','case'),'eisdd':lambda *xs:xs==('frame','lengthunit','timeunit','case'),'se':lambda *xs: norm(xs)==expected}
        assert run('ekbu',values,model)==(which=='rest');cases+=1
    values=base+traces('rest');expected=norm(values)
    for n in ('xb','x4','eisdd','se'):
        assert not run('ekbu',values,model|{n:lambda *xs:False});cases+=1
    for i in range(len(values)):
        altered=values[:];altered[i]='other' if i<5 else c(9) if i<7 else FunctionValue((RS,),RS,lambda t:c(9))
        assert not run('ekbu',altered,model);cases+=1
    for lo,hi in ((0,0),(2,0)):
        altered=values[:];altered[5:7]=[c(lo),c(hi)]
        assert not run('ekbu',altered,model|{'se':lambda *xs:True});cases+=1
    unknowns(lambda mm:run('ekbu',values,mm),model,('xb','x4','se','eisdd'))
    try:run('ekbu',values,model,'full_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole real history was enumerated')
    return dict(cases=cases,whole_interval_rest_distinguishes_drift_and_return=True,unknown_physical_history_rejected=True)

@lru_cache(None)
def point_checks():
    cuts,m=numbers();c,r=cuts.make,cuts.read;cases=0
    fs=[FunctionValue((RS,),RS,lambda t,i=i:c((i+1)*r(t)+2*i)) for i in range(3)]
    for time in (-2,0,3):
        expected=tuple((i+1)*Q(time)+2*i for i in range(3))+(Q(time),)
        region=FunctionValue((RS,)*4,'truth',lambda *xs:tuple(map(r,xs))==expected)
        values=fs+[region,c(time)];assert run('ekbv',values,m);cases+=1
        for i in range(4):
            wrong=tuple(x+1 if j==i else x for j,x in enumerate(expected))
            altered=values[:];altered[3]=FunctionValue((RS,)*4,'truth',lambda *xs,wrong=wrong:tuple(map(r,xs))==wrong)
            assert not run('ekbv',altered,m);cases+=1
        for i in range(4):
            assert not run('ekbv',values,m|{'ba':lambda x,i=i:r(x)!=expected[i]});cases+=1
    unknowns(lambda mm:run('ekbv',values,mm),m,('ba',))
    return dict(cases=cases,same_time_and_three_ordered_coordinates=True)

@lru_cache(None)
def interval_checks():
    truth=lambda *xs:True;cases=0
    # This changes only the diagnostic domain, never the stored Noema quantifier.
    values=['a','a','case','a','a','a','b']+[FunctionValue(('individual',),'individual',lambda t:'a') for _ in range(3)]+[FunctionValue(('individual',)*4,'truth',truth)]
    model={'ekbu':truth,'ba':truth,'lg':truth,'ekbv':truth}
    domain=('a','b')
    assert run('ekbw',values,model,'finite',domain);cases+=1
    for t in domain:
        assert not run('ekbw',values,model|{'ekbv':lambda *xs,t=t:xs[-1]!=t},'finite',domain);cases+=1
    model['lg']=lambda time,lo,hi:time in ('a','b') and (lo,hi)==('a','b')
    assert run('ekbw',values,model|{'ekbv':lambda *xs:xs[-1] in ('a','b')},'finite',domain);cases+=1
    for i in (5,6):
        altered=values[:];altered[i]='b' if i==5 else 'a'
        # An empty artificial interval does not replace the native positive-interval/rest check.
        assert not run('ekbw',altered,model|{'ekbu':lambda *xs:xs[5:7]==('a','b')},'finite',domain);cases+=1
    assert not run('ekbw',values,model|{'ekbu':lambda *xs:False},'finite',domain);cases+=1
    cuts,m=numbers();native=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(LOCATION,fixture('ekbw')[1]))]
    try:run('ekbw',native,m|{'ekbu':truth})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Whole real time replaced by samples')
    return dict(cases=cases,all_times_in_chosen_interval_and_region_guard=True,full_real_domain_refused=True)

def binding_setup():
    cuts,m=numbers();fields=QUESTION+ANSWERS;slots=fixture('ekby')[1]
    values=[n if t=='a' else 'case' if t=='d' else sentinel(s,i+1,cuts) for i,((n,t),(_,s)) in enumerate(zip(fields,slots))];pos={n:i for i,(n,t) in enumerate(fields)}
    def gate(names):
        return lambda *xs:len(xs)==len(names) and all(same_value(x,values[pos[n]],slots[pos[n]][1],cuts) for x,n in zip(xs,names))
    rows={'ekbx':[n for n,t in INVESTIGATION],'ejsn':[n for n,t in CALIBRATION],'eispn':['process','frame','electricfield','magneticfield','region','context']}
    model=m|{n:gate(ns) for n,ns in rows.items()}
    return cuts,values,slots,model,gate

@lru_cache(None)
def binding_checks():
    cuts,values,slots,model,gate=binding_setup();cases=0
    for bits in product((False,True),repeat=3):
        mm=model|{n:model[n] if bit else lambda *xs:False for n,bit in zip(('ekbx','ejsn','eispn'),bits)}
        assert run('ekby',values,mm)==all(bits);cases+=1
    for i,(slot,sort) in enumerate(slots):
        altered=values[:];altered[i]=sentinel(sort,100+i,cuts)
        assert not run('ekby',altered,model);cases+=1
    unknowns(lambda mm:run('ekby',values,mm),model,('ekbx','ejsn','eispn'))
    investigated=values[:len(INVESTIGATION)]
    mm={'ekbw':gate([n for n,t in LOCATION]),'eissd':gate(['observer','wave','process','frame','region','context'])}
    assert run('ekbx',investigated,mm);cases+=1
    for i,(slot,sort) in enumerate(slots[:len(INVESTIGATION)]):
        altered=investigated[:];altered[i]=sentinel(sort,100+i,cuts)
        assert not run('ekbx',altered,mm);cases+=1
    for n in mm:
        assert not run('ekbx',investigated,mm|{n:lambda *xs:False});cases+=1
    unknowns(lambda changed:run('ekbx',investigated,changed),mm,mm)
    return dict(cases=cases,every_observer_wave_process_region_and_calibration_slot_fixed=True,physical_field_pair_not_just_two_numeric_functions=True)

@lru_cache(None)
def question_checks():
    cuts,values,slots,model,gate=binding_setup();n=len(QUESTION);cases=0
    question=run('ekbz',values[:n],model)
    assert isinstance(question,QuestionValue) and len(question.function.parameters)==2;cases+=1
    assert question.function(*values[n:]);cases+=1
    assert not question.function(values[n+1],values[n]);cases+=1
    for i,(slot,sort) in enumerate(slots):
        altered=values[:];altered[i]=sentinel(sort,100+i,cuts)
        candidate=run('ekbz',altered[:n],model)
        assert not candidate.function(*altered[n:]),i;cases+=1
    for name in ('ekbx','ejsn','eispn'):
        unknowns(lambda mm:run('ekbz',values[:n],mm).function(*values[n:]),model,(name,))
    # Constructing a question alone does not assert an answer or execute a physical investigation.
    captured=run('ekbz',values[:n],{name:forbidden for name in model});assert isinstance(captured,QuestionValue);cases+=1
    doc,slotdefs=fixture('ekbz');doc=deepcopy(doc);doc['statements'][0]['body']=doc['statements'][0]['body']['arguments'][0]
    mm=model|{name:lambda x=x:x for (name,s),x in zip(slotdefs,values[:n])}
    try:evaluate_document(doc,individuals=DOMAIN,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('All field functions were finitely enumerated')
    return dict(cases=cases,two_field_answers_keep_all_preselected_question_parameters=True,construction_not_answer_existence_or_success=True,full_function_answer_domain_refused=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][181];assert u['id']=='einstein-1905:u0182' and digest(u['text'].encode())==u['text_sha256']
    return dict(kind='dependency_scope_not_semantic_review',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],resolved_dependencies=list(MEANINGS),unresolved=['先行の31証人と同じ源・波・過程の割当に、固定した質問引数を結ぶ。候補ごとに別の波を存在選択し直さない。','Kとkの同じ相対運動・座標と時刻の変換・新しい領域s6m・単位を接続する。','Wir fragenを著者が実際に質問を提示する関係として接続する。質問を構成するだけで提示済みとしない。','§6の場と§3の座標時刻の両変換の適用、unmittelbar、後続M0325/M0326への前方参照を構成する。','近似的な表示の答えと実際の物理場を区別し、十分性と誤差を維持する。','u0178の見出し及びu0182全体の意味判断。'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==366 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    core=parse(read(CORE));names={d['name'] for d in core['declarations']}
    assert set(MEANINGS)|{'eit2','se','ejsn','eispn','eissd'}<=names
    assert not names&{'cf','seaj','znl','znm','eispp'}
    assert core['statements']==[]
    for style in ('compact','full'):
        body=format_graph(core,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_general_relations=1,all_366_statements_and_prior_meanings_preserved=True,source_question_attribution_not_yet_completed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('rest',rest_checks),('point',point_checks),('interval',interval_checks),('binding',binding_checks),('question',question_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_clock_site_time','check_conductor_cases','check_moving_trip_geometry','check_material_relative_frame','check_distant_wave_source','check_unipolar_machine','compose_wave_display','compose_vacuum_field_domain','compose_material_relative_frame','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{SOURCE,DOC,INVENTORY,*DEPENDENCIES,'scripts/compose_wave_observer_question.py','scripts/check_wave_observer_question.py','tests/test_wave_observer_question.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='stationary_observer_and_field_pair_question_dependencies_checked',document=FULL,**results,remaining=source_record()['unresolved'],verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
