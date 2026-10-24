"""Check speed, local law candidates and the two authored task presentations."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,QuestionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_electron_rest_law_claim as prior
from scripts.check_clock_site_time import relation,perturb
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.compose_electron_moving_law_task import *

DOC='docs/electron-moving-law-task-v1.md';SOURCE='data/einstein-electron-moving-law-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/electron-rest-law-claim-v1.json','reports/point-particle-dynamics-v1.json')
old=prior.old;forbidden=old.forbidden
CONSTANTS=prior.CONSTANTS|{'eisxr':'secondcase','eisxs':'task','eisxu':'speedname'}
PEOPLE=tuple(dict.fromkeys([*prior.PEOPLE,*CONSTANTS.values(),'law','otherlaw','representation','duplicate']))
BOUNDS={'ek4p':{'ek34','ek4m','ek4o'},'ek4q':{'ek4p'},'ek4s':{'ek4p','ek4r'},'ek4t':{'ek4q','ek4h','ek4s'},'ek4v':{'ek4u'},'ek4w':{'ek4p','ek32'},'ek4x':{'ek4w'},'ek4y':{'ek4t','ek4p','ek4x'},'ek42':{'ek4z'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jemarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jempoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jempoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jemcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jemcapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,vs,m):
    doc,slots=fixture(root);assert len(vs)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jempoint':lambda:'case','jemcapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def speed_checks():
    by,m,c,r,key=old.setup();cases=0
    for xyz,s in [((0,0,0),0),((3,4,0),5),((1,2,2),3),((-2,-3,6),7),((Q(1,3),Q(2,3),Q(2,3)),1)]:
        for permutation in (xyz,xyz[1:]+xyz[:1],xyz[2:]+xyz[:2]):
            for speed,want in ((s,True),(-s,s==0),(s+1,False)):
                assert run('ek4n',list(map(c,(speed,*permutation))),m)==want;cases+=1
    functions=[old.fn(old.sort(t),lambda time,a=a,b=b:c(a+b*r(time))) for (n,t),a,b in zip(PROFILES,(1,2,2),(2,0,4))]
    for time,speed in ((0,3),(1,7)):
        point=old.old.point(c,(4,5,6,time));assert run('ek4o',[point,*functions,c(speed)],m);cases+=1
        assert not run('ek4o',[point,*functions,c(speed+1)],m);cases+=1
    for i in range(3):
        changed=functions.copy();changed[i]=old.fn(old.sort(PROFILES[i][1]),lambda t:c(99))
        assert not run('ek4o',[old.old.point(c,(4,5,6,0)),*changed,c(3)],m);cases+=1
    for symbol in ('ba','shv','bd','bg','sca'):
        old.old.reject(lambda:run('ek4n',list(map(c,(3,1,2,2))),m|{symbol:forbidden}),unknown=True);cases+=1
    return dict(cases=cases,nonnegative_three_dimensional_speed_including_zero=True,all_components_at_one_instant=True,no_direction_or_uniform_motion_required=True)

@lru_cache(None)
def setting_checks():
    by,m,c,r,key=old.setup();values=[by[n] for n,t in SETTING];casekey=key(values);cases=0
    for physical,moving,speed in product((False,True),repeat=3):
        mm=m|{'eisxt':lambda:c(7),'ek34':lambda *xs:physical and key(xs)==casekey,'ek4m':lambda *xs:moving and key(xs)==key([by['domain'],by['curve']]),'ek4o':lambda *xs:speed and key(xs)==key([*[by[n] for n,t in REST],c(7)])}
        assert run('ek4p',values,mm)==(physical and moving and speed);cases+=1
    assert r(run('ek4r',values,m|{'eisxt':lambda:c(7)}))==7;cases+=1
    for root,part in [('ek4p','ek34'),('ek4p','ek4m'),('ek4p','ek4o')]:
        mm=m|{'eisxt':lambda:c(7),'ek34':lambda *xs:True,'ek4m':lambda *xs:True,'ek4o':lambda *xs:True,part:forbidden}
        old.old.reject(lambda:run(root,values,mm),unknown=True);cases+=1
    return dict(cases=cases,same_physical_particle_motion_and_speed_setting=True,notation_projects_the_same_bound_speed=True)

@lru_cache(None)
def candidate_checks():
    by,m,c,r,key=old.setup();values=[by[n] for n,t in SETTING];sk=key(values);fk=key([by[n] for n,t in FUTURE]);cases=0
    rows={'vd':{('law','case')},'eisxn':{('law','matter','frame','case')},'eisbi':{('law','frame','case')},'vi':{('law','representation','case'),('law','duplicate','case')}}
    def represented(rep,*xs):return rep in ('representation','duplicate') and key(xs)==sk
    mm=m|{n:relation(rs) for n,rs in rows.items()}|{'ek4p':lambda *xs:key(xs)==sk,'ek32':lambda *xs:key(xs)==fk,'eisxo':represented}
    assert run('ek4w',values+['law'],mm);cases+=1
    cases+=perturb(lambda patch:run('ek4w',values+['law'],patch),mm,rows)
    for symbol in ('ek4p','ek32','eisxo'):
        assert not run('ek4w',values+['law'],mm|{symbol:lambda *xs:False});cases+=1
        old.old.reject(lambda:run('ek4w',values+['law'],mm|{symbol:forbidden}),unknown=True);cases+=1
    def different(spec):
        if spec==old.old.RS:return c(17)
        if spec=='truth':return False
        assert isinstance(spec,dict) and spec['kind']=='function'
        return old.fn(spec,lambda *xs:different(spec['result']))
    for i,(name,typ) in enumerate(SETTING):
        # Supply actual alternative values: the diagnostic key evaluates a few
        # function probes, so an unknown callback is not a swapped known input.
        if typ=='a':changed='other'
        elif typ=='d':changed='other'
        elif typ=='b':changed=Q(17)
        elif typ==R:changed=c(17)
        else:changed=different(old.sort(typ))
        altered=values.copy();altered[i]=changed
        assert not run('ek4w',altered+['law'],mm);cases+=1
        # Hold outer physical/future boundary true to test record correspondence.
        assert not run('ek4w',altered+['law'],mm|{'ek4p':lambda *xs:True,'ek32':lambda *xs:True});cases+=1
    assert not run('ek4w',values+['otherlaw'],mm);cases+=1
    return dict(cases=cases,law_classification_general_validity_and_record_fit_distinct=True,nonempty_all_corresponding_records_required=True,all_setting_roles_reject_swapped_physical_records=True)

@lru_cache(None)
def question_checks():
    by,m,c,r,key=old.setup();values=[by[n] for n,t in SETTING];sk=key(values);cases=0
    for accepted in (set(),{'law'},{'law','otherlaw'}):
        question=run('ek4x',values,{'ek4w':lambda *xs:key(xs[:-1])==sk and xs[-1] in accepted})
        assert isinstance(question,QuestionValue);cases+=1
        for law in ('law','otherlaw','other'):assert question.function(law)==(law in accepted);cases+=1
    question=run('ek4x',values,{'ek4w':forbidden});cases+=1
    old.old.reject(lambda:question.function('law'),unknown=True);cases+=1
    return dict(cases=cases,same_setting_outside_law_candidates=True,empty_single_multiple_answers_without_existence_claim=True,unknown_candidate_not_certified=True)

@lru_cache(None)
def presentation_checks():
    cases=0
    groups=[('ek4s',{'eiswy':{('speedname','ek4p','ek4r','paper','tenth','case')}}),('ek4t',{'ug':{('secondcase','author','ek4q','tenth','case')},'eisxq':{('secondcase','conditional',Q(2),'tenth','case')},'eisra':{('secondcase','author','paper','naming','ek4h','ek4q','tenth','case')}}),('ek4y',{'eisxp':{('task','author','secondcase','ek4t','ek4p','ek4x','tenth','case')}}),('ek4v',{'eir3':{('secondcase','author','paper','ek4u','case')},'ue':{('explanation','secondcase','case')}}),('ek42',{'eir3':{('task','author','paper','ek4z','case')},'ue':{('secondcase','task','case')}})]
    for root,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()}|{'ek4s':lambda:Content(('case','other'),(True,False))}
        cases+=perturb(lambda patch:run(root,[],patch),mm,rows)
        assert run(root,[],mm|{n:forbidden for n in BOUNDS.get(root,set()) if n!='ek4s'});cases+=1
    rows=groups[1][1];mm={n:relation(rs) for n,rs in rows.items()}|{'ek4s':lambda:Content(('case','other'),(False,True))}
    assert not run('ek4t',[],mm);cases+=1
    for root,patch in [('ek4v',{'eisxf':lambda:'secondcase'}),('ek42',{'eisxr':lambda:'task'})]:
        assert not run(root,[],{n:lambda *xs:True for n in ('eir3','ue')}|patch);cases+=1
    return dict(cases=cases,second_case_not_second_particle_or_later_physical_time=True,same_author_prior_hypothesis_and_law_task=True,quoted_candidates_not_executed=True)

@lru_cache(None)
def binder_checks():
    def transform(node):
        if node=='number':return 'individual'
        if isinstance(node,list):return [transform(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jemunit',arguments=[])
        return {k:transform(x) for k,x in node.items()}
    doc=collapse(transform(boundary('ek4q')));doc['declarations'].append(dict(kind='primitive',name='jemunit',parameters=[],result='individual'))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc=extract_document(doc,roots=['ek4q'],statement_indices=[]).document;cases=0
    for pivot in range(len(CASES)):
        f,d,slots,var,body=lifted(doc,'ek4q',pivot,len(CASES),'exists');call=body
        assert call['kind']=='call' and call['symbol']=='ek4p'
        env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
        row=lambda pick:tuple((env|{var:pick})[x['name']] if x['kind']=='variable' else 'a' for x in call['arguments'])
        for selected,want in [(set(),False),({row('a')},True),({row('b')},True)]:
            mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ra':lambda:'a','jemunit':lambda:'a','ek4p':lambda *xs:xs in selected}
            assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_30_existential_setting_slots_checked_with_two_values=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][243];assert u['id']=='einstein-1905:u0244';assert digest(u['text'].encode())==u['text_sha256']
    ms=[m for m in inv['math'] if m['id'] in u['math_ids']]
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    return dict(version='einstein-electron-moving-law-reading-v1',unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),observations=['原刊917頁でu0244のEs besitze nun zweitens、同じ電子、指定時点、速さv、第一文の句点、Wir suchen、同じ時点の直後の時間部分での運動を支配する法則という第二文を続けて照合した。','原刊のvは後続u0245の軸選択に先立つ速度の大きさと読む。法則を数値加速度だけに縮めず、物理法則の成立と同じ初期運動の全記述への適合を候補条件に保持する。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==417 and after.document['statements'][:415]==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[413,414])==selection_binding(before,[413,414]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/electron-rest-law-claim-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert len(MEANINGS)==14 and len(PRIMITIVES)==8
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=14,new_general_relations=4,new_reference_constants=4,new_statements=2,all_415_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('speed',speed_checks),('setting',setting_checks),('candidate',candidate_checks),('question',question_checks),('presentation',presentation_checks),('binder',binder_checks),('structure',structure_checks)]}
    helpers=('compose_point_particle_dynamics','compose_electron_rest_law_claim','check_electron_rest_law_claim','check_point_particle_dynamics','check_attached_material_charge','check_material_acceleration','compose_limits','compose_material_relative_frame','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','check_clock_site_time','check_rod_methods','check_ninth_section_opening','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_moving_law_task.py','scripts/check_electron_moving_law_task.py','tests/test_electron_moving_law_task.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='electron_second_case_and_motion_law_task_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
