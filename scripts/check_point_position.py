"""Check stationary-point scope, Cartesian projections and possible measurements."""
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
from scripts.check_material_relative_frame import arithmetic,RS,FS,IDENTITY,axes,dot,minus,NUM
from scripts.check_rest_frame_introduction import PRIORS as EARLIER
from scripts.compose_point_position import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build

DOC='docs/point-position-v1.md';SOURCE='data/einstein-point-position-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=EARLIER+('data/einstein-rest-frame-review-v1.json',)
DOMAIN=('a','b');POINTS=('reference','setting')

def forbidden(*args):raise ValueError('Unknown point-position input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

def instantiate(doc,name,kind):
    d=deepcopy(next(d for d in doc['declarations'] if d['name']==name));d['name']='jppbody';bound=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind')==kind:
            bound.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    d['body']=walk(d['body']);d['parameters']+=bound;doc['declarations'].append(d)
    assert len(bound)==(2 if name=='eih6' else 7)
    return d['name']

@lru_cache(None)
def fixture(name,boundaries=()):
    root={'rest_body':'eih6','ruler_body':'eiib'}.get(name,name)
    doc=extract_document(parse(read(CORE)),roots=[root],statement_indices=[]).document
    abstract(doc,NUM|set(boundaries))
    if name in ('rest_body','ruler_body'):name=instantiate(doc,root,'forall' if name=='rest_body' else 'exists')
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jpp'+number_word(i);slots.append((n,p['sort']));doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jppcontext',parameters=[],result='situation'))
        body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jppcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots

def evaluate(doc,m):
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,
        primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']

def run(name,values,m,boundaries=(),context='reference'):
    doc,slots=fixture(name,tuple(boundaries));assert len(values)==len(slots);m=dict(m,jppcontext=lambda:context)
    for (n,s),x in zip(slots,values):
        if isinstance(s,dict) and not isinstance(x,FunctionValue):x=FunctionValue(tuple(s['parameters']),s['result'],x)
        m[n]=lambda x=x:x
    return evaluate(doc,m)

def stationary(profile='rest'):
    cuts,m=arithmetic();r=cuts.read
    xyz=lambda t:(Q(2)+(t if profile=='translate' else t*(2-t) if profile=='return' else 0),Q(-3),Q(0))
    fs=[FunctionValue((RS,),RS,lambda t,i=i:cuts.make(xyz(r(t))[i])) for i in range(3)]
    values=['a','b','reference','a','b',cuts.make(Q(0)),cuts.make(Q(2)),*fs]
    scope=('a','b','a','b',Q(0),Q(2),'reference')
    m.update(zm=relation({('b',)}),eirh=relation({('b','a','reference')}),
        eisee=lambda p,f,l,t,lo,hi,c:(p,f,l,t,r(lo),r(hi),c)==scope,
        se=lambda *xs:xs[:5]==tuple(values[:5]) and r(xs[5])==0 and r(xs[6])==2)
    return cuts,m,values

@lru_cache(None)
def rest_checks():
    count=0
    for profile in ('rest','translate','return'):
        cuts,m,args=stationary(profile)
        for a,b in ((0,1),(0,2),(1,2),(2,0),(1,1),(-1,1),(1,3)):
            expected=not(0<=a<=2 and 0<=b<=2) or profile=='rest' or (a==b) or (profile=='return' and a*(2-a)==b*(2-b))
            assert run('rest_body',args+[cuts.make(Q(a)),cuts.make(Q(b))],m,('se',))==expected;count+=1
    cuts,m,args=stationary();values=args+[cuts.make(Q(0)),cuts.make(Q(1))]
    for slot in range(7):
        bad=list(values);bad[slot]=cuts.make(Q(-1)) if slot in (5,6) else ('setting' if slot==2 else 'b' if args[slot]=='a' else 'a')
        assert not run('rest_body',bad,m,('se',));count+=1
    for name in ('zm','eirh','eisee','se'):
        assert not run('rest_body',values,m|{name:lambda *xs:False},('se',));count+=1
        try:run('rest_body',values,m|{name:forbidden},('se',))
        except ValueError as e:assert 'Unknown point-position' in str(e)
        else:raise AssertionError('Unknown rest boundary accepted')
    refused=[]
    for name,vs,bs in (('eih6',args,('se',)),('eiia',args[:3],('se',)),('eiib',['a','b','a','b','reference'],('eigy',))):
        try:run(name,vs,m,bs)
        except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain exceeds' in str(e);refused.append(name)
        else:raise AssertionError('Continuum silently sampled')
    return dict(cases=count,material_point_not_whole_body=True,return_motion_interior_detected=True,context_interval_preserved=True,full_domains_refused=refused,local_instances_not_universal_proof=True)

@lru_cache(None)
def geometry_checks():
    count=0
    for p,o,t in product(((2,-3,0),(0,0,0),(-1,4,5)),((0,0,0),(1,-2,3)),(Q(0),Q(1),Q(1,2))):
        basis=axes(t);out=tuple(dot(minus(p,o),axis) for axis in basis);raw=[*p,*o,*(x for row in basis for x in row),*out]
        cuts,m=arithmetic();vs=[cuts.make(Q(x)) for x in raw]
        assert run('eih7',vs,m);count+=1
        # Independent reconstruction checks the interpretation of all three signed projections.
        assert tuple(sum(out[j]*basis[j][i] for j in range(3)) for i in range(3))==minus(p,o)
        for slot in range(18):
            bad=list(vs);bad[slot]=cuts.make(Q(raw[slot])+1)
            assert not run('eih7',bad,m),(slot,raw);count+=1
    cuts,m=arithmetic();raw=[2,-3,0,1,-2,3,*(x for row in IDENTITY for x in row),1,-1,-3]
    records={'a':[cuts.make(Q(x)) for x in raw]}
    def component(rec,slot):
        if rec not in records or slot.denominator!=1 or not 0<=slot<18:raise ValueError('Unknown record component')
        return records[rec][int(slot)]
    row=('a','b','a','b','reference');m.update(eiseg=relation({row}),eiseh=component)
    assert run('eiic',list(row),m);count+=1
    for slot in range(5):
        bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
        assert not run('eiic',list(row),m|{'eiseg':relation({bad})});count+=1
    for slot in range(18):
        old=records['a'][slot];records['a'][slot]=cuts.make(Q(raw[slot])+1)
        assert not run('eiic',list(row),m);records['a'][slot]=old;count+=1
    unknown=FunctionValue(('number',),'truth',lambda x:x<1)
    try:run('eih7',[unknown,*records['a'][1:]],m)
    except ValueError:pass
    else:raise AssertionError('Unknown real cut probed')
    for rec,slot in (('b',Q(0)),('a',Q(-1)),('a',Q(18)),('a',Q(1,2))):
        try:component(rec,slot)
        except ValueError:pass
        else:raise AssertionError('Unknown component defaulted')
    # Left-handed orthonormal axes remain outside the stated convention.
    bad=list(records['a']);bad[14]=cuts.make(Q(-1));bad[17]=cuts.make(Q(3));assert not run('eih7',bad,m)
    return dict(cases=count,all_signed_components_and_reconstruction=True,rotated_and_translated_auxiliary_chart=True,same_physical_record=True,unknown_inputs_refused=True)

@lru_cache(None)
def measurement_checks():
    count=0;cuts,m=arithmetic();r=cuts.read
    members=FunctionValue(('individual',),'truth',lambda p:p=='a')
    fs=[FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:cuts.make(Q(i)))) for i in range(3)]
    args=['a','b','a','b','reference','a',cuts.make(Q(0)),cuts.make(Q(2)),members,*fs]
    def calibrated(*xs):return xs[:5]==('a','b','a','b','a') and r(xs[5])==0 and r(xs[6])==2 and xs[7]=='reference'
    def rigid(*xs):return xs[:5]==('a','a','reference','b','a') and r(xs[5])==0 and r(xs[6])==2 and all(xs[7](p)==(p=='a') for p in DOMAIN) and all(r(xs[8+i]('a')(cuts.make(Q(1))))==i for i in range(3))
    m.update(eisef=calibrated,eigy=rigid);assert run('ruler_body',args,m,('eigy',));count+=1
    for slot in range(len(args)):
        bad=list(args)
        if slot in (6,7):bad[slot]=cuts.make(Q(-1))
        elif slot==8:bad[slot]=FunctionValue(('individual',),'truth',lambda p:False)
        elif slot>=9:bad[slot]=fs[(slot-9+1)%3]
        else:bad[slot]='setting' if slot==4 else 'a' if args[slot]=='b' else 'b'
        assert not run('ruler_body',bad,m,('eigy',)),slot;count+=1
    for name in ('eisef','eigy'):
        assert not run('ruler_body',args,m|{name:lambda *xs:False},('eigy',));count+=1
    row=('a','b','a','b','a','setting');geom=('a','b','a','b','setting')
    for selected_mask,good_mask in product(range(4),repeat=2):
        selected={p for i,p in enumerate(DOMAIN) if selected_mask&(1<<i)};good={p for i,p in enumerate(DOMAIN) if good_mask&(1<<i)}
        model={'eisei':relation({row}),'eiic':relation({geom}),'eisej':relation({(p,'a','setting') for p in selected}),'eiib':relation({(p,'a','a','b','setting') for p in good})}
        assert run('eiid',list(row),model,('eiic','eiib'))==bool(selected and selected<=good);count+=1
    rows={'eisei':{row},'eiic':{geom},'eisej':{('a','a','setting')},'eiib':{('a','a','a','b','setting')}}
    model={n:relation(rs) for n,rs in rows.items()}
    for name,rs in rows.items():
        original=next(iter(rs))
        for slot in range(len(original)):
            bad=tuple('wrong' if i==slot else x for i,x in enumerate(original))
            assert not run('eiid',list(row),model|{name:relation({bad})},('eiic','eiib'));count+=1
        try:run('eiid',list(row),model|{name:forbidden},('eiic','eiib'))
        except ValueError as e:assert 'Unknown point-position' in str(e)
        else:raise AssertionError('Unknown measurement accepted')
    return dict(cases=count,calibration_and_rigidity_share_full_usage_history=True,nonempty_all_rulers_required=True,single_reused_ruler_allowed=True,same_position_and_cartesian_result=True,unknown_inputs_rejected=True)

@lru_cache(None)
def possibility_checks():
    count=0
    for method,unit,record,setting in product(DOMAIN,DOMAIN,DOMAIN,POINTS):
        allowed=(method,'a','b',unit,'reference',setting);outcome=(method,'a','b',unit,record,setting)
        m={'eisek':relation({allowed}),'eiid':relation({outcome})}
        assert run('eiie',['a','b','reference'],m,('eiid',));count+=1
        for name,row in (('eisek',allowed),('eiid',outcome)):
            for slot in range(len(row)):
                # In-domain substitutions expose mismatches between the two existential witnesses.
                other='setting' if row[slot]=='reference' else 'reference' if row[slot]=='setting' else 'b' if row[slot]=='a' else 'a'
                bad=tuple(other if i==slot else x for i,x in enumerate(row))
                # The outcome record alone is free: replacing it remains a valid existential witness.
                expected=name=='eiid' and slot==4
                assert run('eiie',['a','b','reference'],m|{name:relation({bad})},('eiid',))==expected,(name,slot);count+=1
    for rest_mask,possible_mask in product(range(4),repeat=2):
        rest={p for i,p in enumerate(DOMAIN) if rest_mask&(1<<i)};possible={p for i,p in enumerate(DOMAIN) if possible_mask&(1<<i)}
        m={'ra':lambda:'b','eiia':relation({(p,'b','reference') for p in rest}),'eiie':relation({(p,'b','reference') for p in possible})}
        assert run('eiif',[],m,('eiia','eiie'))==(rest<=possible);count+=1
    m={'eisek':relation({('a','a','b','a','reference','setting')}),'eiid':relation({('a','a','b','a','b','setting')})}
    assert run('eiie',['a','b','reference'],m,('eiid',))
    for name in ('eisek','eiid'):
        try:run('eiie',['a','b','reference'],m|{name:forbidden},('eiid',))
        except ValueError as e:assert 'Unknown point-position' in str(e)
        else:raise AssertionError('Unknown possible execution accepted')
    return dict(cases=count,possible_execution_not_actual_reference_measurement=True,same_method_point_frame_unit_setting_bound=True,all_stationary_points_conditional=True,no_stationary_point_existence_added=True)

@lru_cache(None)
def presentation_checks():
    count=0
    base=dict(eisel=lambda:'a',eised=lambda:'b',rd=lambda:'b',eirf=lambda:'a',ri=lambda:'reference')
    rows={'eir3':{('a','b','a','eiig','reference')},'ue':{('b','a','reference')}}
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:];m=base|{n:relation(rs) for n,rs in rows.items()}
        for bits in product((False,True),repeat=2):
            assert evaluate(doc,m|{n:relation(rs if on else set()) for (n,rs),on in zip(rows.items(),bits)})==all(bits);count+=1
        for n,rs in rows.items():
            row=next(iter(rs))
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row));assert not evaluate(doc,m|{n:relation({bad})});count+=1
        assert not evaluate(doc,m|{'eised':lambda:'a','eir3':lambda *xs:True,'ue':lambda *xs:True});count+=1
    ds={d['name']:d for d in parse(read(CORE))['declarations']};assert ds['eiig']['body']['force']=='assert'
    return dict(cases=count,same_author_document_order=True,quoted_content_not_executed=True,assertive_conditional=True)

def source_record():
    u=json.loads(read(INVENTORY))['units'][8];assert u['id']=='einstein-1905:u0009' and len(u['text'])==242 and not u['math_ids']
    paths={INVENTORY,DOC,'scripts/check_point_position.py','artifacts/einstein-principles-v1/retrieval.json'}
    for row in json.loads(read('artifacts/einstein-principles-v1/retrieval.json'))['sources']:
        assert digest((ROOT/row['path']).read_bytes())==row['sha256'];paths.add(row['path'])
    return dict(version='einstein-point-position-source-reading-v1',reviewer='assistant_visual_and_text_review',source_unit=u['id'],unit_sha256=u['text_sha256'],text=u['text'],range=[0,242],source_nonblank_characters=211,pages=['892'],images=['artifacts/einstein-principles-v1/page-892.jpg'],sentence_ranges=[dict(range=[0,242],text=u['text'],nonblank_characters=211)],math=[],observations=['原刊892頁のRuht ein materieller Punktからausgedrückt werden.までの全一文を画像で視認し固定転記と照合した。','行末分割Koordinaten-systemとaus-gedrücktは転記で接続される。materieller Punkt、starre Maßstäbe、euklidischen Geometrie、kartesischen Koordinatenを確認した。','Ruht … so kann …の条件と可能性、同じ座標系を指すdiesemとletzterem、同じ位置を決め表す二作用を保持する。','数式・著者脚注はない。先行の命名段落と後続の運動・時間の段落は別単位である。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==224
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,indices in zip(PRIORS,([212],[206],[207,208,209,210,211],[213,214,215,216],[217,218],[219],[220],[221,222])):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record();validate_hashes(ROOT,json.loads(read(SOURCE))['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=223,prior_reviews_preserved=True,same_existing_frame=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('rest',rest_checks),('geometry',geometry_checks),('measurement',measurement_checks),('possibility',possibility_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    u=json.loads(read(INVENTORY))['units'][8]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(json.loads(read(SOURCE))['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_point_position.py','scripts/check_point_position.py','tests/test_point_position.py','scripts/check_rest_frame_introduction.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='stationary_material_point_possible_cartesian_measurement_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,242],source=u['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),full_real_domain_evaluated=False,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
