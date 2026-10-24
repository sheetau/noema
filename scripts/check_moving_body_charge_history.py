"""Check actual whole-body totals, nonuniform motion and the two clock histories."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_attached_material_charge as old
from scripts.check_ninth_section_opening import lifted
from scripts.check_convective_foundation_reading import walk
from scripts.compose_moving_body_charge_history import *

DOC='docs/moving-body-charge-history-v1.md';SOURCE='data/einstein-moving-body-charge-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/convective-relativity-claim-v1.json','reports/attached-material-charge-v1.json','reports/material-body-motion-v1.json')
TIMES=(0,1,2,10,12,14);TS=tuple('jmbt'+number_word(i) for i in range(len(TIMES)))
CONSTANTS={'ra':'K','zor':'electriccharge'}
PEOPLE=('a','b','c','body','distribution','K','own','lengthunit','timeunit','chargeunit','electriccharge','other')
BOUNDS={'ek22':set(),'ek23':{'eiad','sb','ek22'},'ek24':set(),'ek25':set(),'ek26':{'ek23'},'ek27':{'sb'},'ek3a':{'sb','ek27'},'ek3b':{'ek23','ek26','eiag','ek25','ek3a'},'ek3c':{'ek24'},'ek3d':{'ek3b','ek3c'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi'}|BOUNDS[root]:doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall') and node['sort']==old.RS:
                probes=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in TS]
                body=probes[-1]
                for p in reversed(probes[:-1]):body=dict(kind='and' if node['kind']=='forall' else 'or',arguments=[p,body])
                return body
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=old.RS) for n in TS]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jmbarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmbpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jmbpoint',arguments=[]))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)]
    return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jmbpoint':lambda:'case'}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],old.forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def setup():
    cuts,m=old.numbers();c,r=cuts.make,cuts.read
    fn=old.fn;sort=old.sort
    by={n:('case' if t=='d' else n) for n,t in SETTING if t in ('a','d')}
    by|=dict(anchor='a',ownframe='own',lower=c(0),upper=c(2),ownlower=c(10),ownupper=c(14),members=fn(old.LS,lambda p:p in ('a','b')))
    for i,a in enumerate(('x','y','z')):
        by[a]=fn(sort(FAMILY),lambda p,i=i:fn(sort(F),lambda t:c((i+1)*r(t)**2+(10 if p=='b' else 0))))
        by['own'+a]=fn(sort(FAMILY),lambda p,i=i:fn(sort(F),lambda t:c(0 if p=='a' else (i+1)*(r(t)-10)**2+10)))
    by['charge']=fn(sort(F),lambda t:c(7));by['owncharge']=fn(sort(F),lambda t:c(-5))
    m|={n:lambda t=t:c(t) for n,t in zip(TS,TIMES)}
    def key(x):
        if isinstance(x,(list,tuple)):return tuple(key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result=='truth':return tuple(x(p) for p in PEOPLE)
        if x.parameters==(old.RS,) and x.result==old.RS:return tuple(r(x(c(t))) for t in TIMES)
        if x.parameters==('individual',) and x.result==sort(F):return tuple(key(x(p)) for p in ('a','b'))
        raise AssertionError(('Unexpected function',x.parameters,x.result))
    def record(side,event,t):
        return key([by['anchor'],event,side['frame'],by['context'],by['lengthunit'],by['timeunit'],c(t),*(side[a](by['anchor'])(c(t)) for a in ('x','y','z'))])
    K=by|dict(frame='K');own=by|{n:by['own'+n] for n,t in SERIES}|dict(frame='own')
    return by,m,c,r,key,K,own,record

def contrasts(root,vs,m,rows,key):
    rel=lambda rs:lambda *xs:key(xs) in rs
    good=m|{n:rel(rs) for n,rs in rows.items()};assert run(root,vs,good),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,good|{n:rel(rs-{row})}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong'
                assert not run(root,vs,good|{n:rel((rs-{row})|{tuple(wrong)})}),(root,n,i);cases+=1
        old.reject(lambda:run(root,vs,good|{n:old.forbidden}),unknown=True);cases+=1
    return cases

@lru_cache(None)
def quantity_checks():
    by,m,c,r,key,K,own,record=setup();cases=0;fn=old.fn;sort=old.sort
    local=K|dict(event='a',time=c(1));amount=local['charge'](local['time'])
    physical=local|dict(kind='electriccharge',part=by['members'],quantityunit=by['chargeunit'],amount=amount)
    rows={'eisvy':{key([physical[n] for n,t in PHYSICAL])}}
    cases+=contrasts('ek22',[local[n] for n,t in LOCAL],m,rows,key)
    for value in (0,-5,7):
        charge=fn(sort(F),lambda t,value=value:c(value));vs=[c(0),c(2),charge]
        assert run('ek24',vs,m);assert run('ek25',vs,m)==(value!=0);cases+=2
    hump=fn(sort(F),lambda t:c(r(t)*(2-r(t))))
    assert not run('ek24',[c(0),c(2),hump],m);cases+=1
    assert not run('ek24',[c(0),c(0),by['charge']],m);cases+=1
    # A constant net total can coexist with changing internal signed amounts.
    internal=lambda t:(c(2+r(t)),c(5-r(t)))
    assert all(r(a)+r(b)==7 for a,b in (internal(c(t)) for t in (0,1,2)))
    assert r(internal(c(0))[0])!=r(internal(c(2))[0]);assert run('ek24',[c(0),c(2),by['charge']],m);cases+=1
    for root,vs in [('ek24',[c(0),c(2),by['charge']]),('ek25',[c(0),c(2),by['charge']])]:old.reject(lambda:run(root,vs,m,'native'));cases+=1
    return dict(cases=cases,physical_whole_material_portion=True,negative_and_zero_totals_distinguished=True,endpoints_alone_not_constant=True,internal_redistribution_not_forbidden=True,unbounded_times_rejected=True)

@lru_cache(None)
def history_checks():
    by,m,c,r,key,K,own,record=setup();cases=0;rel=lambda rs:lambda *xs:key(xs) in rs
    records={record(K,e,t) for e,t in zip(('a','b','c'),(0,1,2))}
    values={key([*(K[n] for n,t in MODEL),e,c(t)]) for e,t in zip(('a','b','c'),(0,1,2))}
    rows={'eiad':{key([K[n] for n,t in HISTORY])},'va':{('K',)},'ek22':values}
    zqn=lambda:old.fn(old.sort('h[a a d] c'),lambda label,dist,ctx:label in ('a','b') and dist=='distribution' and ctx=='case')
    base=m|{'sb':rel(records),'zqn':zqn};cases+=contrasts('ek23',[K[n] for n,t in MODEL],base,rows,key)
    good=base|{n:rel(rs) for n,rs in rows.items()}
    for rec in records:
        assert not run('ek23',[K[n] for n,t in MODEL],good|{'sb':rel(records-{rec})});cases+=1
    # Every extra record of the same event-time role must also carry the whole amount.
    assert not run('ek23',[K[n] for n,t in MODEL],good|{'sb':rel(records|{record(K,'other',1)})});cases+=1
    assert not run('ek23',[K[n] if n!='anchor' else 'other' for n,t in MODEL],good);cases+=1
    old.reject(lambda:run('ek23',[K[n] for n,t in MODEL],good|{'zqn':old.forbidden}),unknown=True);cases+=1
    assert run('ek26',[own[n] for n,t in MODEL],m|{'ek23':lambda *xs:True});cases+=1
    for axis in ('x','y','z'):
        shifted=own|{axis:old.fn(old.sort(FAMILY),lambda p:old.fn(old.sort(F),lambda t:c(1)))}
        assert not run('ek26',[shifted[n] for n,t in MODEL],m|{'ek23':lambda *xs:True});cases+=1
    assert r(K['x']('a')(c(2)))-r(K['x']('a')(c(1)))!=r(K['x']('a')(c(1)))-r(K['x']('a')(c(0)))
    assert r(own['x']('b')(c(14)))!=r(own['x']('b')(c(10)));cases+=2
    return dict(cases=cases,all_times_have_records_and_all_records_have_totals=True,same_distribution_body_units_and_anchor=True,accelerating_K_and_deforming_comoving_coordinates_retained=True,no_all_material_points_at_rest_requirement=True)

@lru_cache(None)
def pair_checks():
    by,m,c,r,key,K,own,record=setup();cases=0;vs=[by[n] for n,t in SETTING];rel=lambda rs:lambda *xs:key(xs) in rs
    local=by|dict(event='b',time=c(1),owntime=c(12))
    rows={'sb':{record(K,'b',1),record(own,'b',12)}}
    cases+=contrasts('ek27',[local[n] for n,t in PAIR],m,rows,key)
    times=list(zip(('a','b','c'),(0,1,2),(10,12,14)))
    records={record(side,e,t) for e,kt,ot in times for side,t in ((K,kt),(own,ot))}
    pairs={key(vs+[e,c(kt),c(ot)]) for e,kt,ot in times}
    cases+=contrasts('ek3a',vs,m|{'sb':rel(records)},{'ek27':pairs},key)
    for side,root_time in ((K,1),(own,12)):
        extra=record(side,'other',root_time)
        assert not run('ek3a',vs,m|{'sb':rel(records|{extra}),'ek27':rel(pairs)});cases+=1
    rows={'ek23':{key([K[n] for n,t in MODEL])},'ek26':{key([own[n] for n,t in MODEL])},'eiag':{key([K[n] for n,t in HISTORY])},'ek25':{key([own[n] for n,t in CONSTANT])},'ek3a':{key(vs)}}
    cases+=contrasts('ek3b',vs,m,rows,key)
    oldkey=key([K[n] for n,t in CONSTANT]);newkey=key([own[n] for n,t in CONSTANT]);assert oldkey!=newkey
    for a,b,want in [(True,True,True),(True,False,False),(False,True,True),(False,False,True)]:
        rs={row for row,on in ((newkey,a),(oldkey,b)) if on}
        assert run('ek3c',vs,m|{'ek24':rel(rs)})==want;cases+=1
    return dict(cases=cases,same_event_different_coordinate_times=True,bidirectional_all_record_correspondence=True,one_body_period_and_distribution_shared=True,only_constancy_transferred_not_numeric_equality=True)

@lru_cache(None)
def binder_checks():
    cases=0
    for pivot in range(len(CASES)):
        doc,d,slots,var,body=lifted(boundary('ek3d'),'ek3d',pivot,len(CASES),'forall')
        calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'};assert calls['ek3b']['arguments']==calls['ek3c']['arguments']
        env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
        rows=lambda picks:{tuple((env|{var:pick})[x['name']] for x in calls['ek3b']['arguments']) for pick in picks}
        for selected,allowed,want in [(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]:
            hs,ls=rows(selected),rows(allowed);mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ek3b':lambda *xs:xs in hs,'ek3c':lambda *xs:xs in ls}
            assert evaluate_document(doc,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_20_setting_binders_shared=True,physical_context_is_one_evaluation_point=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));u=inv['units'][237];math={m['id']:m for m in inv['math']};ms=[math[n] for n in u['math_ids']]
    assert u['id']=='einstein-1905:u0238' and digest(u['text'].encode())==u['text_sha256']
    for m in ms:assert digest(m['mathml'].encode())==m['sha256']
    return dict(version='einstein-moving-body-charge-obligations-v1',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,len(u['text'])],math=ms,semantic_completion=False,connected=['同じ物体・分布・全物質点の任意運動の完全履歴','各系の全区間の実際の全体電荷と一定性','随伴する追跡点と同じ出来事による双方向の期間対応','随伴側で一定ならKでも一定という全設定の条件内容'],unresolved=['先行の展開された方程式との具体的な導出参照','容易に導けるという評価と重要な定理という評価','Es möge noch kurz bemerkt werdenという簡潔な補足の提示','引用符付きの静止系K、auch、コロン後の内容と著者帰属','原刊に戻した全文の通読判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements']==before.document['statements'] and len(after.document['statements'])==412
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[411])==selection_binding(before,[411]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    hypotheses={d['name'] for d in extract_document(core(),roots=['ek3b'],statement_indices=[]).document['declarations']}
    assert not hypotheses&{'ek24','ekx2','ekx3','ekxy','eigy','seni','senh','s46','eiok','eifb','ekyq','semf'}
    assert len(CASES)==20 and len(SETTING)==21
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=10,new_primitives=0,all_412_prior_statements_and_meanings_preserved=True,no_partwise_constancy_or_rigidity_or_uniform_motion_in_setting=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('quantity',quantity_checks),('history',history_checks),('pair',pair_checks),('binder',binder_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_moving_body_charge_history.py','scripts/check_moving_body_charge_history.py','tests/test_moving_body_charge_history.py','scripts/check_attached_material_charge.py','scripts/check_body_rest_field_method.py','scripts/check_ninth_section_opening.py','scripts/check_convective_foundation_reading.py'}
    return dict(status='moving_body_total_charge_content_pending_full_claim',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
