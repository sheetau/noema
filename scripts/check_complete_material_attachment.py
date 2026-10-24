"""Check physical completeness of the material portion domain without rewriting evidence."""
from functools import lru_cache
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_attached_material_charge as old
from scripts.compose_complete_material_attachment import *

DOC='docs/complete-material-attachment-v1.md';SOURCE='data/einstein-complete-material-attachment-obligations-v1.json'
DEPENDENCIES=('reports/attached-material-charge-v1.json',)
BOUNDS={'ekx2':{'ekxv','ekxz','ekxt','ekxu'},'ekx3':{'ekx2','ekxx'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode=='instance':
        assert root=='ekxz'
        count=[]
        def lift(node):
            if isinstance(node,list):return [lift(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='exists':
                assert node['sort']==old.RS;count.append(node)
                d['parameters'].append(dict(name=node['variable'],sort=node['sort']))
                return node['body']
            return {k:lift(v) for k,v in node.items()}
        d['body']=lift(d['body']);assert len(count)==1
    if mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall'):
                ns=next((ns for s,ns in ((old.RS,('jamta','jamtb')),(old.LS,('jampa','jampb','jampc','jampd')),(old.BS,('jamsa','jamsb','jamsc'))) if s==node['sort']),None)
                if ns:
                    probes=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in ns]
                    folded=probes[-1]
                    for probe in reversed(probes[:-1]):folded=dict(kind='and' if node['kind']=='forall' else 'or',arguments=[probe,folded])
                    return folded
            return {k:sample(v) for k,v in node.items()}
        d['body']=sample(d['body'])
    samples={'jamta':old.RS,'jamtb':old.RS,**{n:old.LS for n in ('jampa','jampb','jampc','jampd')},**{n:old.BS for n in ('jamsa','jamsb','jamsc')}}
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in samples.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jamarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots]))]
    return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots)
    mm={n:lambda x=x:x for n,x in old.CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    return evaluate_document(doc,individuals=old.PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],old.forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def amount_checks():
    by,m,c,r,parts,spaces,key,mask=old.setup();cases=0
    by|=dict(kind='electriccharge',quantityunit=by['chargeunit'])
    for amount in (2,-1,0):
        local=by|dict(amount=c(amount));row=key([local[n] for n,t in PHYSICAL]);vs=[local[n] for n,t in ADMISSIBLE]+[local['amount']]
        mm=m|{'eisvy':old.rel({row},key)}
        assert run('ekxz',vs,mm,'instance');cases+=1
        assert not run('ekxz',vs,m|{'eisvy':lambda *xs:False},'instance');cases+=1
        for i in range(len(row)):
            wrong=list(row);wrong[i]='wrong'
            assert not run('ekxz',vs,m|{'eisvy':old.rel({tuple(wrong)},key)},'instance');cases+=1
        old.reject(lambda:run('ekxz',vs,m|{'eisvy':old.forbidden},'instance'),True);cases+=1
    old.reject(lambda:run('ekxz',[by[n] for n,t in ADMISSIBLE],m|{'eisvy':lambda *xs:True},'native'));cases+=1
    return dict(cases=cases,native_existential_body_and_all_physical_slots_checked=True,positive_negative_zero_supported=True,unbounded_amount_and_unknown_input_rejected=True)

@lru_cache(None)
def completeness_checks():
    by,m,c,r,parts,spaces,key,mask=old.setup();values=lambda fs,local=by:[local[n] for n,t in fs];cases=0
    rows={'ekxv':{key(values(FIXED))},'ekxz':set(),'ekxt':set(),'ekxu':set()}
    for time,event in ((0,'a'),(1,'b')):
        local=by|dict(time=c(time),event=event,kind='electriccharge',quantityunit=by['chargeunit'])
        for part in parts:
            loc=local|dict(part=part)
            rows['ekxz'].add(key(values(ADMISSIBLE,loc)));rows['ekxt'].add(key(values(MATERIAL,loc)))
        for space in spaces:rows['ekxu'].add(key(values(SPATIAL,local|dict(space=space))))
    good=m|{n:old.rel(rs,key) for n,rs in rows.items()};vs=values(FIXED)
    assert run('ekx2',vs,good);cases+=1
    for n,rs in rows.items():
        for row in rs:
            assert not run('ekx2',vs,good|{n:old.rel(rs-{row},key)}),(n,'missing');cases+=1
        old.reject(lambda:run('ekx2',vs,good|{n:old.forbidden}),True);cases+=1
    # Every physical reference in admissibility must be passed unchanged.
    row=next(iter(rows['ekxz']))
    for i in range(len(row)):
        wrong=list(row);wrong[i]='wrong'
        assert not run('ekx2',vs,good|{'ekxz':old.rel((rows['ekxz']-{row})|{tuple(wrong)},key)});cases+=1
    coarse=old.fn(old.sort(old.PARTS),lambda part:mask(part) in (0,3));coarseby=by|dict(parts=coarse)
    # The old condition accepts a coarse algebra although actual individual
    # charges exchange one unit. The new condition detects excluded portions.
    def exchanged(*xs):
        loc=dict(zip((n for n,t in MATERIAL),xs));part=loc['part'];time=r(loc['time'])
        actual=(2+time if part('a') else 0)+(-1-time if part('b') else 0)
        return loc['event'] in ('a','b') and r(loc['total'](part))==actual
    common=m|{'eiad':lambda *xs:True,'ejsl':lambda *xs:True,'ekxq':lambda *xs:True,
              'zqn':lambda:old.fn(old.sort('h[a a d] c'),lambda p,dist,ctx:p in ('a','b') and (dist,ctx)==('distribution','case')),
              'ekxt':exchanged,'ekxu':lambda *xs:True}
    assert old.run('ekxq',[by['members'],coarse,by['total']],m,'native',('a','b'));cases+=1
    assert old.run('ekxv',values(FIXED,coarseby),common);cases+=1
    physical=m|{'ekxv':lambda *xs:True,'ekxz':lambda *xs:True,'ekxt':exchanged,'ekxu':lambda *xs:True}
    assert not run('ekx2',values(FIXED,coarseby),physical);cases+=1
    assert not run('ekx2',vs,physical);cases+=1
    # Both directions matter: neither omit finite physical portions nor add
    # portions with no finite physical value. A genuine restricted domain is
    # allowed, unlike an unconditionally all-subsets definition.
    coarsephysical=physical|{'ekxz':lambda *xs:mask(xs[6]) in (0,3)}
    assert not run('ekx2',vs,coarsephysical);cases+=1
    assert run('ekx2',values(FIXED,coarseby),coarsephysical);cases+=1
    # Completeness cannot use an event separate from fixed/spatial amounts.
    split=physical|{'ekxz':lambda *xs:xs[4]=='a','ekxt':lambda *xs:xs[len(FIXED)]=='b'}
    assert not run('ekx2',vs,split);cases+=1
    split=physical|{'ekxz':lambda *xs:xs[4]=='a','ekxt':lambda *xs:xs[len(FIXED)]=='a','ekxu':lambda *xs:xs[len(FIXED)]=='b'}
    assert not run('ekx2',vs,split);cases+=1
    old.reject(lambda:run('ekx2',vs,good,'native'));cases+=1
    return dict(cases=cases,old_coarse_domain_counterexample_reproduced=True,physical_domain_both_directions_checked=True,internal_exchange_rejected=True,one_event_shared_by_completeness_material_and_space=True,continuous_domains_not_silently_sampled=True)

@lru_cache(None)
def shared_checks():
    by,m,c,r,parts,spaces,key,mask=old.setup();vs=[by[n] for n,t in ALL]
    rows={'ekx2':{key([by[n] for n,t in FIXED])},'ekxx':{key([by[n] for n,t in SMALL])}}
    mm=m|{n:old.rel(rs,key) for n,rs in rows.items()};assert run('ekx3',vs,mm);cases=1
    for name,rs in rows.items():
        row=next(iter(rs));assert not run('ekx3',vs,mm|{name:lambda *xs:False});cases+=1
        for i in range(len(row)):
            wrong=list(row);wrong[i]='wrong'
            assert not run('ekx3',vs,mm|{name:old.rel({tuple(wrong)},key)});cases+=1
        old.reject(lambda:run('ekx3',vs,mm|{name:old.forbidden}),True);cases+=1
    return dict(cases=cases,all_attachment_and_rigidity_references_shared=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read(old.SOURCE))
    return dict(version='einstein-complete-material-attachment-obligations-v1',kind='dependency_scope_not_semantic_review',unit=previous['unit'],unit_sha256=previous['unit_sha256'],text=previous['text'],resolved_dependencies=list(MEANINGS),reading='物理的な有限部分保有量が存在する全物質部分と選択部分族を、同じ時刻・出来事で双方向に一致させて不変な付着を読む。前版の粗い選択だけで不変性が成立するとしない。',unresolved=previous['unresolved'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (old.INVENTORY,old.FACSIMILE,DOC,old.SOURCE)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==408 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[407])==selection_binding(before,[407])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/attached-material-charge-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in core()['declarations']};assert set(MEANINGS)|{'eisvy','ekxv','ekxt','ekxu','ekxx'}<=names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=3,new_general_relations=0,all_408_statements_meanings_and_original_evidence_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('amount',amount_checks),('completeness',completeness_checks),('shared',shared_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_complete_material_attachment.py','scripts/check_complete_material_attachment.py','tests/test_complete_material_attachment.py','scripts/check_attached_material_charge.py'}
    return dict(status='physically_complete_material_attachment_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
