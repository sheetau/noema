"""Check mathematical descriptions independently of physical truth and prior grasp."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS,FS,NUM
from scripts.check_point_position import PRIORS as EARLIER
from scripts.compose_motion_time_description import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDICES,build

DOC='docs/motion-time-description-v1.md';SOURCE='data/einstein-motion-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';READING='data/motion-time-description-reading-v1.json'
PRIORS=EARLIER+('data/einstein-point-position-review-v1.json',)
DOMAIN=('a','b');POINTS=('before','now')

def forbidden(*args):raise ValueError('Unknown motion-time-description input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

def instantiated(doc,root):
    d=deepcopy(next(d for d in doc['declarations'] if d['name']==root));d['name']='jmtbody';bound=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')=='exists':
            bound.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=bound;doc['declarations'].append(d);assert len(bound)==8
    return d['name']

def math_at(doc):
    # Instantiate the actual la body at a supplied real time, retaining all guards.
    la=deepcopy(next(d for d in doc['declarations'] if d['name']=='la'));assert la['body']['kind']=='forall'
    la['name']='jmtlocal';la['parameters'].append(dict(name=la['body']['variable'],sort=la['body']['sort']));la['body']=la['body']['body'];doc['declarations'].append(la)
    d=deepcopy(next(d for d in doc['declarations'] if d['name']=='eiij'));d['name']='jmtmath'
    d['parameters'].append(dict(name='jtime',sort=RS))
    def walk(node):
        if isinstance(node,list):
            for x in node:walk(x)
        elif isinstance(node,dict):
            if node.get('kind')=='call' and node.get('symbol')=='la':node['symbol']='jmtlocal';node['arguments'].append(dict(kind='variable',name='jtime'))
            else:
                for x in node.values():walk(x)
    walk(d['body']);doc['declarations'].append(d);return d['name']

@lru_cache(None)
def fixture(name,boundaries=()):
    root={'math_at':'eiij','giving_body':'eiil','class_body':'eiip'}.get(name,name)
    doc=extract_document(parse(read(CORE)),roots=[root],statement_indices=[]).document;abstract(doc,NUM|{'bg'}|set(boundaries))
    if name=='math_at':name=math_at(doc)
    elif name in ('giving_body','class_body'):name=instantiated(doc,root)
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jmt'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jmtcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jmtcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']

def run(name,values,m,boundaries=(),context='now'):
    doc,slots=fixture(name,tuple(boundaries));assert len(values)==len(slots);m=dict(m,jmtcontext=lambda:context)
    for (n,s),x in zip(slots,values):
        if isinstance(s,dict) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        m[n]=lambda x=x:x
    return evaluate(doc,m)

def numerical(profile='linear'):
    cuts,m=arithmetic();r=cuts.read;m['bg']=lambda a,b:r(a)<r(b)
    phase=lambda t:t if profile=='linear' else t*(2-t) if profile=='return' else Q(0)
    xyz=lambda t:(Q(2)+phase(t),-2*phase(t),Q(-3))
    fs=[FunctionValue((RS,),RS,lambda t,i=i:cuts.make(xyz(r(t))[i])) for i in range(3)]
    return cuts,m,[cuts.make(Q(0)),cuts.make(Q(2)),*fs]

@lru_cache(None)
def mathematical_checks():
    count=0
    for profile in ('linear','return','constant'):
        cuts,m,args=numerical(profile)
        for t in (Q(-1),Q(0),Q(1,2),Q(1),Q(2),Q(3)):
            assert run('math_at',args+[cuts.make(t)],m);count+=1
        for slot in (0,1):
            bad=list(args);bad[slot]=cuts.make(Q(2) if slot==0 else Q(0));assert not run('math_at',bad+[cuts.make(Q(1))],m);count+=1
        for axis in range(3):
            bad=list(args);bad[axis+2]=FunctionValue((RS,),RS,lambda t:cuts.make(Q(999)))
            model=m|{n:lambda x:cuts.read(x)!=999 for n in ('ba','zzba')}
            assert not run('math_at',bad+[cuts.make(Q(1))],model);count+=1
            # Values outside the selected interval are not required by this description.
            assert run('math_at',bad+[cuts.make(Q(3))],model);count+=1
    cuts,m,args=numerical();unknown=FunctionValue(('number',),'truth',lambda x:x<1)
    try:run('math_at',[unknown,*args[1:],cuts.make(Q(1))],m)
    except ValueError:pass
    else:raise AssertionError('Unknown cut probed')
    refused=[]
    for name,values in (('eiij',args),('eiil',['a','a','b','now','b']),('eiip',['a','b','b','now'])):
        try:run(name,values,m|{'eiseo':lambda *xs:True})
        except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e);refused.append(name)
        else:raise AssertionError('Real/function domain finitely sampled')
    return dict(cases=count,all_three_coordinate_functions=True,constant_and_nonuniform_trajectories_allowed=True,full_domains_refused=refused,local_instances_not_universal_proof=True,unknown_cut_rejected=True)

def encode(cuts,x,sort):
    if sort==RS:return cuts.read(x)
    if sort==FS:return tuple(cuts.read(x(cuts.make(Q(t)))) for t in (0,1,2))
    return value(x)

@lru_cache(None)
def description_checks():
    cuts,m,math=numerical();record=['a','b','a','now','a','b',*math]
    doc,slots=fixture('eiik',('eiij',));sorts=[s for _,s in slots];expected=tuple(encode(cuts,x,s) for x,s in zip(record,sorts))
    def matches(*xs):return tuple(encode(cuts,x,s) for x,s in zip(xs[:-1],sorts))==expected and value(xs[-1])=='se'
    m.update(zm=relation({('a',)}),eirh=relation({('a','b','now')}),eiij=lambda *xs:True,eisem=matches)
    assert run('eiik',record,m,('eiij',));count=1
    for slot in range(len(record)):
        bad=list(record)
        if slot in (6,7):bad[slot]=cuts.make(Q(-1))
        elif slot>=8:bad[slot]=math[2+(slot-8+1)%3]
        else:bad[slot]='before' if slot==3 else 'b' if record[slot]=='a' else 'a'
        assert not run('eiik',bad,m,('eiij',)),slot;count+=1
    for n in ('zm','eirh','eiij','eisem'):
        assert not run('eiik',record,m|{n:lambda *xs:False},('eiij',));count+=1
        try:run('eiik',record,m|{n:forbidden},('eiij',))
        except ValueError as e:assert 'Unknown motion-time-description' in str(e)
        else:raise AssertionError('Unknown description accepted')
    # se is quoted as the fidelity criterion; it is never evaluated by recording the functions.
    for truth in (False,True):
        assert run('eiik',record,m|{'se':lambda *xs:truth},('eiij',));count+=1
    return dict(cases=count,same_point_frame_units_period_and_functions=True,material_point_not_space_point=True,physical_history_criterion_quoted_not_executed=True)

@lru_cache(None)
def giving_and_class_checks():
    count=0;cuts,m,math=numerical()
    # Native existential bodies, with the infinite witnesses supplied explicitly.
    for name,args in (('giving_body',['a','b','a','now','b','a','a','b',*math]),('class_body',['a','a','b','now','b','a','b',*math])):
        record=['a','b','a','now','a','b',*math]
        sorts=[s for _,s in fixture('eiik',('eiij',))[1]];expected=tuple(encode(cuts,x,s) for x,s in zip(record,sorts))
        def record_row(*xs):return tuple(encode(cuts,x,s) for x,s in zip(xs,sorts))==expected
        rows={'eiseo':{('a','b','now')}}
        if name=='giving_body':rows['eisep']={('a','a','b','now')}
        model=m|{'eiik':record_row}|{n:relation(rs) for n,rs in rows.items()}
        assert run(name,args,model,('eiik',));count+=1
        for slot,(_,sort) in enumerate(fixture(name,('eiik',))[1]):
            bad=list(args)
            if sort==RS:bad[slot]=cuts.make(Q(-1))
            elif sort==FS:bad[slot]=FunctionValue((RS,),RS,lambda t:cuts.make(Q(123)))
            else:bad[slot]='before' if sort=='situation' else 'b' if args[slot]=='a' else 'a'
            assert not run(name,bad,model,('eiik',)),(name,slot);count+=1
        for n in ('eiik',*rows):
            assert not run(name,args,model|{n:lambda *xs:False},('eiik',));count+=1
    for material,intention,given in product(range(4),repeat=3):
        members={p for i,p in enumerate(DOMAIN) if material&(1<<i)};wanted={p for i,p in enumerate(DOMAIN) if intention&(1<<i)};supplied={p for i,p in enumerate(DOMAIN) if given&(1<<i)}
        model={'ra':lambda:'a','rd':lambda:'b','eirf':lambda:'a','eiii':relation({(p,'now') for p in members}),'eisen':relation({('b',p,'a','a','now') for p in wanted}),'eiil':relation({('b',p,'a','now','a') for p in supplied})}
        assert run('eiim',[],model,('eiii','eiil'))==((members&wanted)<=supplied);count+=1
    return dict(cases=count,native_existential_bodies_bind_all_fields=True,giving_not_function_existence_alone=True,description_class_not_filtered_by_physical_meaning=True,conditional_method_without_actual_intention_added=True)

@lru_cache(None)
def prior_understanding_checks():
    count=0
    for agent,record,doc,interpretation in product(DOMAIN,repeat=4):
        rows={'eiser':{(interpretation,record,doc,'now')},'zm4':{('before','now')},'eises':{(agent,interpretation,record,doc,'before')}}
        model={n:relation(rs) for n,rs in rows.items()};values=[agent,record,doc,'now']
        assert run('eiiq',values,model);count+=1
        for n,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                other='now' if row[slot]=='before' else 'before' if row[slot]=='now' else 'b' if row[slot]=='a' else 'a'
                bad=tuple(other if i==slot else x for i,x in enumerate(row))
                assert not run('eiiq',values,model|{n:relation({bad})}),(n,slot);count+=1
        assert not run('eiiq',values,model|{'zm4':relation({('now','before')})});count+=1
    # Unknownness is not a successful prior understanding, nor an inferred negative fact.
    for n in model:
        try:run('eiiq',values,model|{n:forbidden})
        except ValueError as e:assert 'Unknown motion-time-description' in str(e)
        else:raise AssertionError('Unknown understanding accepted')
    return dict(cases=count,same_interpretation_user_record_document=True,strictly_prior_not_simultaneous_or_later=True,unknown_inputs_rejected=True)

@lru_cache(None)
def necessary_condition_checks():
    count=0;base={'ra':lambda:'a','eirf':lambda:'b'}
    for selected,meaning,understood in product(range(4),repeat=3):
        chosen={r for i,r in enumerate(DOMAIN) if selected&(1<<i)}
        physical={a for i,a in enumerate(DOMAIN) if meaning&(1<<i)};clear={a for i,a in enumerate(DOMAIN) if understood&(1<<i)}
        model=base|{'eiip':relation({(r,'a','b','now') for r in chosen}),'eiseq':relation({(a,r,'b','now') for a in physical for r in DOMAIN}),'eiiq':relation({(a,r,'b','now') for a in clear for r in DOMAIN})}
        assert run('eiir',[],model,('eiip','eiiq'))==(not chosen or physical<=clear);count+=1
    # Both records are selected, but prior understanding of another record cannot substitute.
    rows={'eiip':{(r,'a','b','now') for r in DOMAIN},'eiseq':{('a','a','b','now')},'eiiq':{('a','a','b','now')}}
    model=base|{n:relation(rs) for n,rs in rows.items()};assert run('eiir',[],model,('eiip','eiiq'));count+=1
    for slot in range(4):
        row=next(iter(rows['eiiq']));bad=tuple(('before' if i==3 else 'b' if x=='a' else 'a') if i==slot else x for i,x in enumerate(row))
        assert not run('eiir',[],model|{'eiiq':relation({bad})},('eiip','eiiq'));count+=1
    return dict(cases=count,prior_grasp_necessary_not_sufficient=True,all_descriptions_and_users_scoped=True,no_actual_physical_meaning_or_understanding_asserted=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for path in (CORE,FULL):
        original=parse(read(path))
        for which,node,msg,before in ((0,'a','eiin','b'),(1,'b','eiis','a')):
            doc=dict(original,statements=[original['statements'][-2+which]])
            rows={'eir3':{(node,'a','b',msg,'now')},'ue':{(before,node,'now')}}
            if which:rows['zei']={(node,'a','b','now')}
            base={'eiset':lambda:'a','eiseu':lambda:'b','eisel':lambda:'b','rd':lambda:'a','eirf':lambda:'b','ri':lambda:'now'};model=base|{n:relation(rs) for n,rs in rows.items()}
            for bits in product((False,True),repeat=len(rows)):
                assert evaluate(doc,model|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
            for n,rs in rows.items():
                row=next(iter(rs))
                for slot in range(len(row)):
                    bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,model|{n:relation({bad})});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']}
    assert all(ds[n]['body']['force']=='assert' for n in ('eiin','eiis'))
    return dict(cases=count,author_document_order_preserved=True,attention_separate_from_truth=True,quoted_contents_not_executed=True)

def source_record():
    u=json.loads(read(INVENTORY))['units'][9];assert u['id']=='einstein-1905:u0010' and len(u['text'])==666 and not u['math_ids']
    paths={INVENTORY,DOC,'scripts/check_motion_time_description.py','artifacts/einstein-principles-v1/retrieval.json'}
    for row in json.loads(read('artifacts/einstein-principles-v1/retrieval.json'))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-motion-time-source-reading-v1',reviewer='assistant_visual_and_text_review',source_unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'][:337],range=[0,337],source_nonblank_characters=286,pages=['892'],images=['artifacts/einstein-principles-v1/page-892.jpg'],sentence_ranges=[dict(range=[a,b],text=u['text'][a:b],nonblank_characters=sum(not c.isspace() for c in u['text'][a:b])) for a,b in ((0,126),(127,337))],math=[],observations=['原刊892頁末尾のWollen wirからverstanden wird.までの前二文を保存画像と固定転記で照合した。','第一文の行末分割be-schreibenを接続する。BewegungとZeitの強調を、対象の運動と時間変数を区別する説明へ反映した。','第二文のerst dann … wennとvorher、注意喚起im Auge zu behalten、引用されたZeitを確認した。数式・著者脚注はない。','次頁に続くWir haben以降の後二文はこの照合の範囲外で、段落全体の完成は未主張。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==226
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220],[221,222],[223])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    reading=json.loads(read(READING));validate_hashes(ROOT,reading['source_sha256']);assert reading['selection']==selection_binding(new,INDICES) and reading['source_nonblank_characters']==286
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=224,prior_reviews_preserved=True,whole_paragraph_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    from scripts.review_motion_time_description import build_reading
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')
    write_exact(ROOT/READING,json.dumps(build_reading(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('mathematics',mathematical_checks),('description',description_checks),('giving_and_class',giving_and_class_checks),('prior_understanding',prior_understanding_checks),('necessary_condition',necessary_condition_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][9]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,READING,*PRIORS,'scripts/compose_motion_time_description.py','scripts/check_motion_time_description.py','scripts/review_motion_time_description.py','tests/test_motion_time_description.py','scripts/compose_point_position.py','scripts/check_point_position.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='time_function_description_and_prior_time_understanding_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[a,b],source=u['text'][a:b],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for a,b in ((0,126),(127,337))]),full_real_domain_evaluated=False,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['後二文の時間判断と同時的出来事','列車と時計の引用例','段落全体の意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
