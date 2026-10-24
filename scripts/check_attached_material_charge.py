"""Distinguish fixed material charge from constant body totals and fixed spatial boxes."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_body_rest_field_method import numbers,point
from scripts.check_material_relative_frame import NUM,RS
from scripts.compose_attached_material_charge import *

DOC='docs/attached-material-charge-v1.md';SOURCE='data/einstein-attached-material-charge-obligations-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p916-0.jpg'
DEPENDENCIES=('reports/convective-charge-setting-v1.json','reports/additive-charge-v1.json','reports/material-body-motion-v1.json','reports/rigid-body-kinematics-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'t','zor':'electriccharge'}
PEOPLE=tuple(dict.fromkeys([*CONSTANTS.values(),*[n for n,t in ALL+MATERIAL if t=='a'],'a','b','other']))
BOUNDS={'ekxt':{'ekxr'},'ekxu':{'ekxt'},'ekxv':{'eiad','ejsl','ekxq','ekxt','ekxu'},'ekxx':{'eigy','ekxw'},'ekxy':{'ekxv','ekxx'}}
def sort(t):return parse('n:r jam[] '+t+'.')['declarations'][0]['result']
LS=sort(LABELS);BS=sort(BALL);PS=sort(POINT)
def fn(s,body):return FunctionValue(tuple(s['parameters']),s['result'],body)
def forbidden(*xs):raise ValueError('Unknown attached-charge input')
def reject(call,unknown=False):
    try:call()
    except ValueError as e:assert ('Unknown attached-charge input' in str(e)) if unknown else any(s in str(e) for s in ('rational number domain','Finite function domain')),str(e)
    else:raise AssertionError('Unknown or unbounded input accepted')

@lru_cache(None)
def core():return parse(read(CORE))
def replace(node,name,term):
    if isinstance(node,list):return [replace(x,name,term) for x in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable' and node['name']==name:return deepcopy(term)
    return {k:replace(v,name,term) for k,v in node.items()}

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in (NUM|{'bg','bj','szi'}|BOUNDS.get(root,set())):
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    doc=extract_document(doc,roots=[root],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==root)
    if mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('exists','forall'):
                names=next((ns for s,ns in ((RS,('jamta','jamtb')),(LS,('jampa','jampb','jampc','jampd')),(BS,('jamsa','jamsb','jamsc'))) if s==node['sort']),None)
                if root=='ekxx' and node['sort']=='individual':names=('jamlaba','jamlabb')
                if names:
                    probes=[sample(replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in names]
                    folded=probes[-1]
                    for probe in reversed(probes[:-1]):folded=dict(kind='and' if node['kind']=='forall' else 'or',arguments=[probe,folded])
                    return folded
            return {k:sample(v) for k,v in node.items()}
        d['body']=sample(d['body'])
    samples={'jamta':RS,'jamtb':RS,'jamlaba':'individual','jamlabb':'individual',**{n:LS for n in ('jampa','jampb','jampc','jampd')},**{n:BS for n in ('jamsa','jamsb','jamsc')}}
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in samples.items()]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jamarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    body=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jamcapture',parameters=[d['result']],result='truth'));body=dict(kind='call',symbol='jamcapture',arguments=[body])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive')
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def run(root,vs,m,mode='sample',domain=PEOPLE):
    doc,slots=fixture(root,mode);assert len(slots)==len(vs),(root,len(slots),len(vs));captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}|{'jamcapture':capture}
    answer=evaluate_document(doc,individuals=domain,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else answer

def setup():
    cuts,m=numbers();c,r=cuts.make,cuts.read
    parts=[fn(LS,lambda p,mask=mask:p in ('a','b') and bool(mask & (1 if p=='a' else 2))) for mask in range(4)]
    mask=lambda part:sum(bit for p,bit in (('a',1),('b',2)) if part(p))
    by={n:n for n,t in ALL+MATERIAL if t=='a'}|dict(context='case',lower=c(0),upper=c(2),time=c(0),threshold=c(4),members=parts[3],part=parts[1])
    for i,a in enumerate(('x','y','z')):
        by[a]=fn(sort(FAMILY),lambda p,i=i:fn(sort('h['+R+'] '+R),lambda t:c((i+1)*(r(t)+(1 if p=='b' else 0)))))
    amount=lambda part:c((2 if part('a') else 0)-(1 if part('b') else 0))
    by|={'parts':fn(sort(PARTS),lambda p:True),'total':fn(sort(TOTAL),amount)}
    spaces=[fn(BS,lambda p:False),fn(BS,lambda p:True),fn(BS,lambda p:r(p('x'))<Q(3,2))];by['space']=spaces[2]
    m|={'jamta':lambda:c(0),'jamtb':lambda:c(1),'jamlaba':lambda:'a','jamlabb':lambda:'b'}|{n:lambda p=p:p for n,p in zip(('jampa','jampb','jampc','jampd'),parts)}|{n:lambda p=p:p for n,p in zip(('jamsa','jamsb','jamsc'),spaces)}
    probes=[point(c,(0,0,0,0)),point(c,(1,2,3,0)),point(c,(2,4,6,1))]
    def key(x):
        if isinstance(x,(list,tuple)):return tuple(key(y) for y in x)
        if not isinstance(x,FunctionValue):return x
        if x.parameters==('number',):return r(x)
        if x.parameters==('individual',) and x.result=='truth':return mask(x)
        if x.parameters==(PS,) and x.result=='truth':return tuple(x(p) for p in probes)
        while isinstance(x,FunctionValue):
            f=x.implementation;code=getattr(f,'__code__',None)
            if code is None:return f
            closed=dict(zip(code.co_freevars,(cell.cell_contents for cell in (getattr(f,'__closure__',None) or ()))))
            if 'raw' not in closed:return f
            x=closed['raw']
        return x
    return by,m,c,r,parts,spaces,key,mask
def rel(rows,key):return lambda *xs:key(xs) in rows
def contrasts(root,vs,m,rows,key):
    mm=m|{n:rel(rs,key) for n,rs in rows.items()};assert run(root,vs,mm);cases=1
    for name,rs in rows.items():
        for row in rs:
            assert not run(root,vs,mm|{name:rel(rs-{row},key)}),(root,name);cases+=1
            for i in range(len(row)):
                wrong=list(row);wrong[i]='wrong'
                assert not run(root,vs,mm|{name:rel((rs-{row})|{tuple(wrong)},key)}),(root,name,i);cases+=1
        reject(lambda:run(root,vs,mm|{name:forbidden}),True);cases+=1
    return cases

@lru_cache(None)
def measure_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0
    for a,b in ((2,-1),(2,-2),(0,0),(-3,-2)):
        total=fn(sort(TOTAL),lambda p,a=a,b=b:c((a if p('a') else 0)+(b if p('b') else 0)))
        assert run('ekxq',[parts[3],by['parts'],total],m,'native',('a','b'));cases+=1
    for bad in (lambda p:c(1 if mask(p)==0 else 0),lambda p:c(9 if mask(p)==3 else 0)):
        assert not run('ekxq',[parts[3],by['parts'],fn(sort(TOTAL),bad)],m,'native',('a','b'));cases+=1
    incomplete=fn(sort(PARTS),lambda p:mask(p)!=3)
    assert not run('ekxq',[parts[3],incomplete,by['total']],m,'native',('a','b'));cases+=1
    # b is outside this universe. Totals may not distinguish it.
    assert not run('ekxq',[parts[1],by['parts'],by['total']],m,'native',('a','b'));cases+=1
    return dict(cases=cases,native_all_subsets_of_two_labels_checked=True,signed_cancellation_empty_value_additivity_and_extensionality=True)

@lru_cache(None)
def pullback_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0
    for time,want in ((0,3),(1,1),(2,0)):
        local=by|{'time':c(time)};result=run('ekxs',[local[n] for n,t in PULLBACK],m)
        assert mask(result)==want;assert not result('other');cases+=2
    # Inspect each coordinate from the very same material label and time.
    for who,offset in (('a',0),('b',1)):
        expected=(1+offset,2*(1+offset),3*(1+offset),1)
        for slot in range(4):
            space=fn(BS,lambda p,slot=slot:p is not None and r(p(('x','y','z','t')[slot]))==expected[slot])
            local=by|dict(time=c(1),space=space)
            assert run('ekxs',[local[n] for n,t in PULLBACK],m)(who);cases+=1
            wrong=fn(BS,lambda p,slot=slot:r(p(('x','y','z','t')[slot]))==expected[slot]+1)
            local['space']=wrong;assert not run('ekxs',[local[n] for n,t in PULLBACK],m)(who);cases+=1
    return dict(cases=cases,same_material_label_all_four_coordinates=True,fixed_spatial_box_selects_different_material_at_different_times=True)

@lru_cache(None)
def binding_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0;values=lambda fs:[by[n] for n,t in fs]
    amount=by['total'](by['part'])
    rows={'ekxr':{key([by['members'],by['parts'],by['total'],by['part'],amount])},
          'eisvy':{key([by[n] if n not in ('kind','quantityunit','amount') else 'electriccharge' if n=='kind' else by['chargeunit'] if n=='quantityunit' else amount for n,t in PHYSICAL])}}
    cases+=contrasts('ekxt',values(MATERIAL),m,rows,key)
    preimage=run('ekxs',values(PULLBACK),m);amount=by['total'](preimage)
    rows={'ekxt':{key([by[n] if n!='part' else preimage for n,t in MATERIAL])},
          'eisvx':{key([by[n] for n in ('distribution',)]+['electriccharge']+[by[n] for n in ('frame','event','time','space','lengthunit','timeunit','chargeunit')]+[amount,'case'])}}
    cases+=contrasts('ekxu',values(SPATIAL),m,rows,key)
    return dict(cases=cases,physical_material_and_spatial_amounts_share_all_references=True,quantity_kind_units_time_and_direction_preserved=True)

@lru_cache(None)
def fixed_checks():
    by,m,c,r,parts,spaces,key,mask=setup();values=lambda fs:[by[n] for n,t in fs]
    mm=m|{'eiad':lambda *xs:True,'ejsl':lambda *xs:True,'ekxq':lambda *xs:True,
          'zqn':lambda:fn(sort('h[a a d] c'),lambda p,dist,ctx:p in ('a','b') and (dist,ctx)==('distribution','case'))}
    rows={'ekxt':set(),'ekxu':set()}
    for time,event in ((0,'a'),(1,'b')):
        local=by|dict(time=c(time),event=event)
        rows['ekxt']|={key([local[n] if n!='part' else part for n,t in MATERIAL]) for part in parts}
        rows['ekxu']|={key([local[n] if n!='space' else space for n,t in SPATIAL]) for space in spaces}
    # Missing one portion or spatial inverse image at either time must fail.
    good=mm|{n:rel(rs,key) for n,rs in rows.items()};vs=values(FIXED);assert run('ekxv',vs,good);cases=1
    for n,rs in rows.items():
        for row in rs:assert not run('ekxv',vs,good|{n:rel(rs-{row},key)});cases+=1
        reject(lambda:run('ekxv',vs,good|{n:forbidden}),True);cases+=1
    # Same total 2 + (-1) = 3 + (-2), but a unit transfers between parts.
    def exchanged(*xs):
        local=dict(zip((n for n,t in MATERIAL),xs));part=local['part'];time=r(local['time'])
        actual=(2+time if part('a') else 0)+(-1-time if part('b') else 0)
        return key(xs) in rows['ekxt'] and r(local['total'](part))==actual
    assert not run('ekxv',vs,good|{'ekxt':exchanged});cases+=1
    # One common event must cover BOTH families at each time.
    separated=mm|{'ekxt':lambda *xs:xs[len(FIXED)]=='a','ekxu':lambda *xs:xs[len(FIXED)]=='b'}
    assert not run('ekxv',vs,separated);cases+=1
    for name in ('body','frame','distribution','chargeunit','context'):
        bad=by|{name:'other'};assert not run('ekxv',[bad[n] for n,t in FIXED],good);cases+=1
    bad=by|{'parts':fn(sort(PARTS),lambda part:mask(part)!=3)}
    assert not run('ekxv',[bad[n] for n,t in FIXED],mm|{'ekxt':lambda *xs:True,'ekxu':lambda *xs:True});cases+=1
    bad=by|{'upper':c(0)};assert not run('ekxv',[bad[n] for n,t in FIXED],mm|{'ekxt':lambda *xs:True,'ekxu':lambda *xs:True});cases+=1
    reject(lambda:run('ekxv',vs,good,'native'));cases+=1
    return dict(cases=cases,all_parts_and_times_use_one_fixed_charge_function=True,constant_total_with_internal_exchange_rejected=True,one_shared_event_for_material_and_spatial_families=True,unbounded_time_and_space_not_silently_sampled=True)

@lru_cache(None)
def size_checks():
    by,m,c,r,parts,spaces,key,mask=setup();cases=0
    def coords(delta):return {a:fn(sort(FAMILY),lambda p,i=i:fn(sort('h['+R+'] '+R),lambda time:c(delta[i] if p=='b' else 0))) for i,a in enumerate(('x','y','z'))}
    for threshold,want in ((-1,False),(0,False),(1,False),(2,False),(3,True)):
        local=by|coords((2,0,0))|dict(left='a',right='b',threshold=c(threshold))
        assert run('ekxw',[local[n] for n,t in PAIR],m)==want;cases+=1
    for delta in ((2,0,0),(0,2,0),(0,0,2),(1,2,2)):
        local=by|coords(delta)|dict(left='a',right='b',threshold=c(3))
        assert run('ekxw',[local[n] for n,t in PAIR],m)==(delta!=(1,2,2));cases+=1
    rows={'eigy':{key([by[n] for n,t in HISTORY])},'eisvz':{key([by[n] for n,t in SCALE])},'ekxw':set()}
    for left in ('a','b'):
        for right in ('a','b'):
            for time in (0,1):
                local=by|dict(left=left,right=right,time=c(time));rows['ekxw'].add(key([local[n] for n,t in PAIR]))
    # Restrict individual quantifier probes to the actual two members, keeping
    # unrelated physical references as parameters rather than an N^3 search.
    cases+=contrasts('ekxx',[by[n] for n,t in SMALL],m,rows,key)
    rows={'ekxv':{key([by[n] for n,t in FIXED])},'ekxx':{key([by[n] for n,t in SMALL])}}
    cases+=contrasts('ekxy',[by[n] for n,t in ALL],m,rows,key)
    return dict(cases=cases,native_three_axis_distances_and_strict_threshold_checked=True,smallness_requires_prior_context_scale_and_rigidity=True,same_body_interval_members_and_coordinates_shared=True)

@lru_cache(None)
def source_record():
    u=json.loads(read(INVENTORY))['units'][231];assert u['id']=='einstein-1905:u0232' and digest(u['text'].encode())==u['text_sha256']
    return dict(version='einstein-attached-material-charge-obligations-v1',kind='dependency_scope_not_semantic_review',unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],resolved_dependencies=list(MEANINGS),reading='不変な結合を全物質部分の電荷不変と、その物質運動による空間保有量の変化として読む。小ささは先に指定する文脈尺度、剛性は指定評価系での全点対距離の不変とする。',unresolved=['複数の局所担体分布と場の全分布ekxmの分解・合成','各担体の評価系と場の系の対応','イオン・電子という括弧内の担体の読み','Lorentzの電気力学と動く物体の光学の電磁的基礎という条件付き位置付け','u0227–u0232の著者提示・式・説明・見出しの統合'],whole_unit_reviewed=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==408 and new.document['statements']==old.document['statements']
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    assert selection_binding(new,[407])==selection_binding(old,[407])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/convective-charge-setting-identifiers-v1.json'))['entries']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    names={d['name'] for d in core()['declarations']}
    assert set(MEANINGS)|{'eisvx','eisvy','eisvz','eigy','eigw','eiad','eirh','ejsl','zqn'}<=names
    assert not names&{'eiah','eiaq','semf','ekbw','ekbx','ekby','ekbz'}
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=12,new_general_relations=2,all_408_statements_and_meanings_preserved=True,no_stationarity_sphere_or_global_rigidity_assumed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('measure',measure_checks),('pullback',pullback_checks),('binding',binding_checks),('fixed',fixed_checks),('size',size_checks),('structure',structure_checks)]}
    helpers=('compose_limits','compose_material_relative_frame','compose_material_body_motion','compose_field_equations','compose_local_density','compose_additive_charge','compose_doppler_infinity','check_body_rest_field_method','check_material_relative_frame','check_tau_differential','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_attached_material_charge.py','scripts/check_attached_material_charge.py','tests/test_attached_material_charge.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='fixed_material_charge_on_small_rigid_body_connected',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
