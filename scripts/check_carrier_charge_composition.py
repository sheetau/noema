"""Check finite signed folds, complete partitions and physical regional composition."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_attached_material_charge as old
from scripts.compose_carrier_charge_composition import *

DOC='docs/carrier-charge-composition-v1.md';SOURCE='data/einstein-carrier-charge-composition-obligations-v1.json'
DEPENDENCIES=('reports/complete-material-attachment-v1.json','reports/convective-charge-setting-v1.json')
BOUNDS={'ekyb':{'eiac'},'ekyc':{'ekyb','ekx3'},'ekyd':{'ekya'},'ekye':{'ekxe','ekyb','ekyd'},'ekyf':{'ekxj','ekye','ekyc'}}
SEQUENCES=((),('a',),('b',),('a','b'),('b','a'),('a','a'),('other',))
seq=lambda xs:SequenceValue(tuple(xs),json.dumps('individual'))
PEOPLE=tuple(dict.fromkeys([*old.PEOPLE,*(n for n,t in COUPLED_FAMILY if t=='a'),'componenta','componentb','framea','frameb']))

@lru_cache(None)
def core():return parse(read(CORE))

def reject(call,unknown=False):
    try:call()
    except ValueError as e:assert ('Unknown attached-charge input' in str(e)) if unknown else any(s in str(e) for s in ('rational number domain','Finite function domain','unbounded sequence domain')),str(e)
    else:raise AssertionError('Unknown/unbounded input accepted')

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.NUM|{'bg','bj','szi','lb'}|BOUNDS.get(root,set()):
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    samples={'jaabodya':'individual','jaabodyb':'individual','jaaea':old.RS,'jaaeb':old.RS,**{'jaaseq'+number_word(i):old.sort(LIST) for i in range(len(SEQUENCES))},**{n:old.BS for n in ('jamsa','jamsb','jamsc')}}
    # Explicitly probe the two material/body labels. Physical reference names
    # remain valid individuals without becoming a cubic carrier search.
    def individuals(node):
        if isinstance(node,list):return [individuals(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind') in ('exists','forall') and node['sort']=='individual':
            probes=[individuals(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in ('jaabodya','jaabodyb')]
            return dict(kind='and' if node['kind']=='forall' else 'or',arguments=probes)
        return {k:individuals(v) for k,v in node.items()}
    for decl in doc['declarations']:
        if decl['kind']=='definition':decl['body']=individuals(decl['body'])
    if mode!='native':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall'):
                names=[n for n,s in samples.items() if s==node['sort'] and (mode!='epsilon' or s==old.RS)]
                if names:
                    probes=[sample(old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names]
                    folded=probes[-1]
                    for probe in reversed(probes[:-1]):folded=dict(kind='and' if node['kind']=='forall' else 'or',arguments=[probe,folded])
                    return folded
            return {k:sample(v) for k,v in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in samples.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jaaarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jaacapture',parameters=[d['result']],result='truth'));body=dict(kind='call',symbol='jaacapture',arguments=[body])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots),(root,len(vs),len(slots));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in old.CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}|{'jaacapture':capture}
    value=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],old.forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else value

def setup():
    base,m,c,r,parts,spaces,key,mask=old.setup()
    def dummy(s,seed):
        if s=='truth':return True
        if s=='individual':return 'reference'+str(seed)
        if s=='situation':return 'case'
        if s=='number':return Q(seed)
        if s==old.RS:return c(seed)
        return old.fn(s,lambda *xs:dummy(s['result'],seed))
    by={n:dummy(old.sort(t),i+1) for i,(n,t) in enumerate(COUPLED_FAMILY)}
    by|={n:n for n,t in COUPLED_FAMILY if t=='a'};by['context']='case'
    by|=dict(carriers=parts[3],components=old.fn(old.sort(COMPONENTS),lambda p:'component'+p),portions=old.fn(old.sort(PORTIONS),lambda p:parts[1 if p=='a' else 2]),weights=old.fn(old.sort(WEIGHTS),lambda p:c(2 if p=='a' else -1)),value=c(1),kind='electriccharge',quantityunit='chargeunit',time=c(0))
    by['point']=old.point(c,(0,0,0,0));by['total']=old.fn(old.sort(dict(REGIONAL_TOTAL)['total']),lambda space:c(1))
    by['sets']=old.fn(old.sort(dict(REGIONAL_TOTAL)['sets']),lambda space:True)
    by['amounts']=old.fn(old.sort(AMOUNTS),lambda space:by['weights'])
    for n,t in OWN:
        if n=='frame':f=lambda p:'frame'+p
        elif n in ('lower','upper','threshold'):f=lambda p,n=n:base[n]
        else:f=lambda p,n=n:base[n]
        by['own'+n]=old.fn(old.sort(t),f)
    m|={'jaabodya':lambda:'a','jaabodyb':lambda:'b','jaaea':lambda:c(Q(1,4)),'jaaeb':lambda:c(Q(1,2)),'lb':lambda x,y,e:abs(r(x)-r(y))<r(e)}
    m|={'jaaseq'+number_word(i):lambda xs=xs:seq(xs) for i,xs in enumerate(SEQUENCES)}
    return by,m,c,r,parts,spaces,key,mask

def contrasts(root,vs,m,rows,key):
    mm=m|{n:old.rel(rs,key) for n,rs in rows.items()};assert run(root,vs,mm),root;cases=1
    for n,rs in rows.items():
        for row in rs:
            assert not run(root,vs,mm|{n:old.rel(rs-{row},key)}),(root,n,'missing');cases+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong'
                assert not run(root,vs,mm|{n:old.rel((rs-{row})|{tuple(wrong)},key)}),(root,n,i);cases+=1
        reject(lambda:run(root,vs,mm|{n:old.forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def sum_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0
    for xs in SEQUENCES:
        for body in ('a','b','other'):
            assert run('ekx4',[seq(xs),body],m)==(body in xs);cases+=1
        want=all(x in ('a','b') for x in xs) and len(set(xs))==len(xs)
        assert run('ekx5',[by['carriers'],seq(xs)],m)==want;cases+=1
    for a,b in ((2,-1),(2,-2),(0,0),(-3,-2)):
        weights=old.fn(old.sort(WEIGHTS),lambda p,a=a,b=b:c(a if p=='a' else b))
        for xs in SEQUENCES[:-1]:
            assert r(run('ekx6',[weights,seq(xs)],m))==sum(a if p=='a' else b for p in xs);cases+=1
        assert run('ekya',[by['carriers'],weights,c(a+b)],m);cases+=1
        for wrong in (a+b+1,a+b-1):assert not run('ekya',[by['carriers'],weights,c(wrong)],m);cases+=1
    for base in SEQUENCES:
        for extension in SEQUENCES:
            selected=lambda xs:all(x in ('a','b') for x in xs) and len(set(xs))==len(xs)
            assert run('ekx7',[by['carriers'],seq(base),seq(extension)],m)==(selected(base) and selected(extension) and set(base)<=set(extension));cases+=1
    assert run('ekya',[parts[0],by['weights'],c(0)],m);cases+=1
    assert not run('ekya',[parts[0],by['weights'],c(1)],m);cases+=1
    for mode in ('native','epsilon'):
        reject(lambda:run('ekya',[by['carriers'],by['weights'],by['value']],m,mode));cases+=1
    return dict(cases=cases,native_folds_empty_signed_cancelled_and_duplicate_inputs=True,all_sampled_finite_extensions_and_permutations_checked=True,infinite_real_and_sequence_domains_refused=True)

@lru_cache(None)
def partition_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0
    pairs={('a','componenta'),('b','componentb'),('a','distribution'),('b','distribution')}
    def model(pairs=pairs):return m|{'zqn':lambda:old.fn(old.sort('h[a a d] c'),lambda label,dist,ctx:ctx=='case' and (label,dist) in pairs),'eiac':lambda body,ctx,portion:ctx=='case' and mask(portion)==(1 if body=='a' else 2)}
    values=lambda local:[local[n] for n,t in PARTITION]
    assert run('ekyb',values(by),model());cases+=1
    for pair in pairs:assert not run('ekyb',values(by),model(pairs-{pair}));cases+=1
    for name in ('distribution','context'):
        assert not run('ekyb',values(by|{name:'other'}),model());cases+=1
    assert not run('ekyb',values(by|{'carriers':parts[1]}),model());cases+=1
    # A purported whole body with no members is refused by the physical boundary.
    assert not run('ekyb',values(by|{'portions':old.fn(old.sort(PORTIONS),lambda p:parts[0])}),model());cases+=1
    overlap=by|{'portions':old.fn(old.sort(PORTIONS),lambda p:parts[3])}
    bothpairs={(p,d) for p in ('a','b') for d in ('componenta','componentb','distribution')}
    assert not run('ekyb',values(overlap),model(bothpairs)|{'eiac':lambda *xs:True});cases+=1
    assert run('ekyb',values(by|{'carriers':parts[0]}),model(set()));cases+=1
    reject(lambda:run('ekyb',values(by),model()|{'eiac':old.forbidden}),True);cases+=1
    rows={'ekyb':{key(values(by))},'ekx3':set()}
    for body in ('a','b'):
        vals=[body if n=='body' else by['components'](body) if n=='distribution' else by['portions'](body) if n=='members' else by[n] if n in SHARED else by['own'+n](body) for n,t in ALL]
        rows['ekx3'].add(key(vals))
    cases+=contrasts('ekyc',[by[n] for n,t in ATTACHED],m,rows,key)
    return dict(cases=cases,complete_disjoint_physical_material_partition=True,empty_global_distribution_and_neutral_members_supported=True,each_carrier_has_its_own_frame_history_and_charge_function=True)

@lru_cache(None)
def physical_checks():
    by,m,c,r,parts,spaces,key,mask=setup();local=by|dict(region=spaces[2]);cases=0
    rows={'ekya':{key([by['carriers'],by['weights'],by['value']])},'eisvx':set()}
    for dist,amount in [('distribution',by['value']),('componenta',c(2)),('componentb',c(-1))]:
        row=local|dict(distribution=dist,amount=amount);rows['eisvx'].add(key([row[n] for n,t in AMOUNT]))
    cases+=contrasts('ekyd',[local[n] for n,t in REGIONAL],m,rows,key)
    rows={'ekxe':{key([by[n] for n,t in REGIONAL_TOTAL])},'ekyb':{key([by[n] for n,t in PARTITION])},'ekyd':set()}
    for space in spaces:
        row=by|dict(kind='electriccharge',time=by['point']('t'),region=space,quantityunit=by['chargeunit'],weights=by['amounts'](space),value=by['total'](space))
        rows['ekyd'].add(key([row[n] for n,t in REGIONAL]))
    cases+=contrasts('ekye',[by[n] for n,t in TOTAL],m,rows,key)
    reject(lambda:run('ekye',[by[n] for n,t in TOTAL],m|{n:old.rel(rs,key) for n,rs in rows.items()},'native'));cases+=1
    rows={n:{key([by[k] for k,t in fs])} for n,fs in [('ekxj',COUPLED),('ekye',TOTAL),('ekyc',ATTACHED)]}
    cases+=contrasts('ekyf',[by[n] for n,t in COUPLED_FAMILY],m,rows,key)
    return dict(cases=cases,local_and_global_physical_charge_share_frame_event_time_region_kind_and_units=True,all_selected_regions_use_same_carrier_family=True,density_equations_and_local_rigidity_share_complete_arguments=True)

@lru_cache(None)
def source_record():
    previous=json.loads(read('data/einstein-complete-material-attachment-obligations-v1.json'))
    return dict(version='einstein-carrier-charge-composition-obligations-v1',kind='dependency_scope_not_semantic_review',unit=previous['unit'],unit_sha256=previous['unit_sha256'],text=previous['text'],resolved_dependencies=list(MEANINGS),reading='各担体の全物質点を全分布へ分割し、各局所成分と全分布の同じ系・時刻・領域の電荷を順序に依存しない総和で結ぶ。各担体の剛性評価系と場の系は区別する。',unresolved=['場の全領域の局所証人への適用と、各担体の評価系における同じ物質点・出来事・履歴期間の座標対応',*previous['unresolved'][2:]],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (old.INVENTORY,old.FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert len(after.document['statements'])==408 and after.document['statements']==before.document['statements']
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[407])==selection_binding(before,[407]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/complete-material-attachment-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in core()['declarations']};assert set(MEANINGS)|{'eisvx','eiac','zqn','ekx3','ekxj','ekxe'}<=names
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=10,new_general_relations=0,all_408_statements_meanings_and_original_evidence_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('sum',sum_checks),('partition',partition_checks),('physical',physical_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_carrier_charge_composition.py','scripts/check_carrier_charge_composition.py','tests/test_carrier_charge_composition.py','scripts/check_attached_material_charge.py'}
    return dict(status='complete_carrier_partition_and_signed_regional_charge_composition_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
