"""Check future-side dynamics, shared notation and the restricted authored premise."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_point_particle_dynamics as old
from scripts.check_clock_site_time import relation,perturb,unknowns
from scripts.check_rod_methods import value
from scripts.check_ninth_section_opening import lifted
from scripts.check_problem_series_reduction import collapse
from scripts.check_convective_foundation_reading import walk
from scripts.compose_electron_rest_law_claim import *

DOC='docs/electron-rest-law-claim-v1.md';SOURCE='data/einstein-electron-rest-law-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';FACSIMILE='artifacts/written-facsimiles-v1/einstein-p917-0.jpg'
DEPENDENCIES=('reports/point-particle-dynamics-v1.json','reports/material-acceleration-v1.json','reports/rest-frame-introduction-v1.json')
CONSTANTS=old.CONSTANTS|{'eisxa':'intro','eisxb':'naming','eisxc':'assumption','eisxd':'conditional','eisxe':'display','eisxf':'explanation','eisxg':'tenth','eisxh':'matter','eisxi':'electron','eisxj':'charge_name','eisxk':'coordinates','eisxl':'mass_name','eisxm':'heading','rd':'author','eirf':'paper','ri':'case'}
PEOPLE=tuple(dict.fromkeys([*old.PEOPLE,*CONSTANTS.values()]))
BOUNDS={'ek3z':{'sjs','senz'},'ek32':{'sjs','senz'},'ek33':{'ek3r','ek3t','ek32'},'ek34':{'ek3v'},'ek35':{'ek34','ek33'},'ek36':{'ek34','ek4m'},'ek4c':{'ek34','ek37','ek4a','ek4b'},'ek4d':{'ek36'},'ek4f':{'ek35'},'ek4g':{'ek35'},'ek4h':{'ek4e','ek4f','ek4c','ek4g'},'ek4j':{'ek4i'},'ek4l':{'ek4k'}}
forbidden=old.forbidden;fn=old.fn;sort=old.sort

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def boundary(root):
    doc=extract_document(core(),roots=[root],statement_indices=[]).document
    for i,d in enumerate(doc['declarations']):
        if d['kind']=='definition' and d['name'] in old.old.NUM|{'bg','bj','szi'}|BOUNDS.get(root,set()):doc['declarations'][i]=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    return extract_document(doc,roots=[root],statement_indices=[]).document

@lru_cache(None)
def fixture(root,mode='sample'):
    doc=deepcopy(boundary(root));d=next(d for d in doc['declarations'] if d['name']==root)
    if root=='ek4f' and mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='forall' and isinstance(node['sort'],dict) and node['sort']['kind']=='description':
                terms=[dict(kind='quote',body=dict(kind='call',symbol=n,arguments=[])) for n in ('ek35','ek36')]
                probes=[old.old.replace(node['body'],node['variable'],term) for term in terms]
                return dict(kind='and',arguments=probes)
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body']);doc['declarations'].insert(0,dict(kind='primitive',name='ek36',parameters=[],result='content'))
    if root=='ek4m' and mode=='sample':
        def sample(node):
            if isinstance(node,list):return [sample(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='exists' and node['sort']==old.old.RS:
                probes=[sample(old.old.replace(node['body'],node['variable'],dict(kind='call',symbol=n,arguments=[]))) for n in old.TS];out=probes[-1]
                for p in reversed(probes[:-1]):out=dict(kind='or',arguments=[p,out])
                return out
            return {k:sample(x) for k,x in node.items()}
        d['body']=sample(d['body'])
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=old.old.RS) for n in old.TS]
    slots=[]
    for i,p in enumerate(d['parameters']):
        n='jerarg'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=root,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jerpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jerpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jercapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jercapture',arguments=[expr])
    doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(root,vs,m,mode='sample'):
    doc,slots=fixture(root,mode);assert len(vs)==len(slots);captured=[]
    def capture(x):captured.append(x);return True
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jerpoint':lambda:'case','jercapture':capture}|m|{n:lambda x=x:x for n,x in zip(slots,vs)}
    result=evaluate_document(doc,individuals=PEOPLE,situations=('case','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']
    return captured[0] if captured else result

@lru_cache(None)
def future_checks():
    by,m,c,r,key=old.setup();cases=0
    for cut in (-1,0,1):
        right=run('ek3y',[by['domain'],c(cut)],m)
        for t in (-3,-2,-1,Q(-1,2),0,Q(1,2),1,2,3):
            assert right(c(t))==(abs(t)<2 and t>=cut);cases+=1
    # The derivative interpretation recognizes only this actual Noema domain
    # constructor and registered analytical polynomials, never inferred probes.
    decl=next(d for d in core()['declarations'] if d['name']=='ek3y')
    domain_impl=old.analytic.unwrap(by['domain']).implementation
    polynomials={}
    def polynomial(coeff):
        f=fn(sort(PROFILES[0][1]),lambda t:c(sum(Q(a)*r(t)**i for i,a in enumerate(coeff))))
        polynomials[old.analytic.unwrap(f).implementation]=tuple(map(Q,coeff));return f
    def derivative(domain,velocity,time,acceleration):
        free=old.analytic.free(old.analytic.unwrap(domain))
        if free.get('node')!=decl['body']:raise ValueError('Unknown right-domain syntax')
        env=free['captured'];base,cutoff=[env[p['name']] for p in decl['parameters']]
        if old.analytic.unwrap(base).implementation is not domain_impl:raise ValueError('Unknown original time domain')
        coeff=polynomials.get(old.analytic.unwrap(velocity).implementation)
        if coeff is None:raise ValueError('Unknown analytical velocity')
        t=r(time);wanted=sum(i*a*t**(i-1) for i,a in enumerate(coeff) if i)
        return abs(t)<2 and r(cutoff)==t and r(acceleration)==wanted
    mm=m|{'senz':lambda domain,t:old.analytic.unwrap(domain).implementation is domain_impl and abs(r(t))<2,'sjs':derivative}
    for coeff in ((0,2),(1,-3,4),(0,0,0,2)):
        velocity=polynomial(coeff)
        for t in (-1,0,1):
            a=sum(i*Q(x)*Q(t)**(i-1) for i,x in enumerate(coeff) if i)
            assert run('ek3z',[by['domain'],velocity,c(t),c(a)],mm)
            assert not run('ek3z',[by['domain'],velocity,c(t),c(a+1)],mm);cases+=2
    b=by.copy()
    for (n,t),a in zip(PROFILES,(2,-4,6)):b[n]=polynomial((0,a,1))
    assert run('ek32',[b[n] for n,t in FUTURE],mm);cases+=1
    for n,t in ACCEL:
        assert not run('ek32',[(c(r(b[n])+1) if name==n else b[name]) for name,t in FUTURE],mm);cases+=1
    for n,t in PROFILES:
        assert not run('ek32',[(polynomial((0,99)) if name==n else b[name]) for name,t in FUTURE],mm);cases+=1
    assert not run('ek32',[(old.old.point(c,(1,2,3,1)) if name=='point' else b[name]) for name,t in FUTURE],mm);cases+=1
    for name in ('senz','sjs'):
        old.old.reject(lambda:run('ek3z',[by['domain'],polynomial((0,2)),c(0),c(2)],mm|{name:forbidden}),unknown=True);cases+=1
    return dict(cases=cases,native_future_domain_keeps_base_point_and_excludes_past=True,registered_polynomial_right_derivative=True,same_time_three_velocity_functions_and_accelerations=True,general_real_limits_proved=False)

@lru_cache(None)
def content_checks():
    by,m,c,r,key=old.setup();cases=0
    for rest,law,future in product((False,True),repeat=3):
        mm=m|{'ek3r':lambda *xs:rest,'ek3t':lambda *xs:law,'ek32':lambda *xs:future}
        assert run('ek33',[by[n] for n,t in SETTING],mm)==((not rest) or (law and future));cases+=1
    mm=m|{'ek3v':lambda *xs:key(xs)==key([by[n] for n,t in SETTING])}
    assert run('ek34',[by[n] for n,t in SETTING],mm);cases+=1
    for patch in ({'eisxh':lambda:'other'},{'ra':lambda:'other'}):assert not run('ek34',[by[n] for n,t in SETTING],mm|patch);cases+=1
    assert run('ek4m',[by[n] for n,t in MOTION],m);cases+=1
    fixed=fn(sort(CURVE),lambda t:old.old.point(c,(1,2,3,r(t))))
    assert not run('ek4m',[by['domain'],fixed],m);cases+=1
    for axis in range(3):
        moving=fn(sort(CURVE),lambda t,axis=axis:old.old.point(c,tuple(r(t)**2 if i==axis else 0 for i in range(3))+(r(t),)))
        assert run('ek4m',[by['domain'],moving],m);cases+=1
    one=fn(sort(DOMAIN),lambda t:r(t)==0)
    assert not run('ek4m',[one,by['curve']],m);cases+=1
    old.old.reject(lambda:run('ek4m',[by[n] for n,t in MOTION],m,mode='native'));cases+=1
    for root,target in [('ek37','charge'),('ek4a','point'),('ek4b','mass')]:
        actual=run(root,[by[n] for n,t in SETTING],m);assert key(actual)==key(by[target]);cases+=1
    parts=('ek4e','ek4f','ek4c','ek4g')
    for truths in product((False,True),repeat=4):
        mm={n:lambda x=x:Content(('case','other'),(x,not x)) for n,x in zip(parts,truths)}|{'ue':lambda *xs:True}
        assert run('ek4h',[],mm)==all(truths);cases+=1
    return dict(cases=cases,same_particle_frame_and_parameter_projections=True,position_change_allows_instantaneous_rest=True,right_initial_change_is_conditional=True,whole_presentation_one_context=True)

@lru_cache(None)
def premise_checks():
    rows={'ug':{('assumption','author','ek35','tenth','case')},'eiswx':{('assumption','author','matter','ek35','tenth','case')}}
    mm={n:relation(rs) for n,rs in rows.items()};cases=perturb(lambda m:run('ek4f',[],m),mm,rows)
    extra=rows['eiswx']|{('assumption','author','matter','ek36','tenth','case')}
    assert not run('ek4f',[],mm|{'eiswx':relation(extra)});cases+=1
    assert run('ek4f',[],mm|{'ek35':forbidden,'ek36':forbidden});cases+=1
    try:run('ek4f',[],mm,mode='native')
    except ValueError as e:assert 'Cannot finitely quantify the description domain' in str(e)
    else:raise AssertionError('All assumption descriptions finitely certified')
    return dict(cases=cases,required_same_independent_law_and_no_extra_law=True,background_not_counted_as_added_dynamical_premise=True,native_description_domain_not_enumerated=True)

@lru_cache(None)
def presentation_checks():
    groups=[('ek4c',{'eiswy':{('charge_name','ek34','ek37','paper','tenth','case'),('mass_name','ek34','ek4b','paper','tenth','case')},'eiswz':{('coordinates',('x','y','z'),'ek34','ek4a','paper','tenth','case')}}),('ek4d',{'eisd3':{('intro','matter','paper','case')},'ug':{('intro','author','ek36','tenth','case')}}),('ek4e',{'eisd4':{('naming','author','electron','matter','paper','case')}}),('ek4g',{'eisox':{('display','ek35','case')},'uf':{('author',a,b,'case') for a,b in [('assumption','conditional'),('conditional','display'),('display','explanation'),('explanation','display')]},'ue':{(a,b,'case') for a,b in [('assumption','conditional'),('conditional','display'),('display','explanation')]}}),('ek4j',{'eir3':{('intro','author','paper','ek4i','case')},'ue':{('heading','intro','case')}}),('ek4l',{'eir3':{('naming','author','paper','ek4k','case')},'ue':{('intro','naming','case')}})]
    cases=0
    for root,rows in groups:
        mm={n:relation(rs) for n,rs in rows.items()};cases+=perturb(lambda m:run(root,[],m),mm,rows)
        assert run(root,[],mm|{n:forbidden for n in BOUNDS.get(root,set())});cases+=1
    for root,patch in [('ek4j',{'eisxm':lambda:'intro'}),('ek4l',{'eisxa':lambda:'naming'})]:
        assert not run(root,[],{n:lambda *xs:True for n in ('eir3','ue')}|patch);cases+=1
    return dict(cases=cases,naming_targets_same_hypothetical_particle=True,all_quantities_use_one_setting_and_ordered_spatial_axes=True,colon_display_and_where_explanation_connected=True,quoted_physics_not_executed=True)

@lru_cache(None)
def binder_checks():
    cases=0
    for root,kind in [('ek35','forall'),('ek36','exists')]:
        def transform(node):
            if node=='number':return 'individual'
            if isinstance(node,list):return [transform(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='call' and node.get('symbol')=='bb':return dict(kind='call',symbol='jerunit',arguments=[])
            return {k:transform(x) for k,x in node.items()}
        doc=collapse(transform(boundary(root)));doc['declarations'].append(dict(kind='primitive',name='jerunit',parameters=[],result='individual'))
        doc['declarations'].sort(key=lambda d:d['kind']!='primitive');doc=extract_document(doc,roots=[root],statement_indices=[]).document
        for pivot in range(len(CASES)):
            f,d,slots,var,body=lifted(doc,root,pivot,len(CASES),kind)
            calls={x['symbol']:x for x in walk(body) if x.get('kind')=='call'}
            if root=='ek35':assert calls['ek34']['arguments']==calls['ek33']['arguments']
            env={p['name']:'case' if p['sort']=='situation' else 'a' for p in d['parameters']}
            row=lambda symbol,pick:tuple((env|{var:pick})[x['name']] if x['kind']=='variable' else 'a' for x in calls[symbol]['arguments'])
            if root=='ek35':variants=[(('a','b'),('a','b'),True),(('a','b'),('a',),False),(('b',),('a',),False),((),(),True)]
            else:variants=[(('b',),('b',),True),((),('a','b'),False),(('b',),(),False)]
            for selected,allowed,want in variants:
                law='ek33' if root=='ek35' else 'ek4m';hs={row('ek34',x) for x in selected};ls={row(law,x) for x in allowed}
                mm={n:lambda x=env[p['name']]:x for n,p in zip(slots,d['parameters'])}|{'ra':lambda:'a','jerunit':lambda:'a','ek34':lambda *xs:xs in hs,law:lambda *xs:xs in ls}
                assert evaluate_document(f,individuals=('a','b'),situations=('case','other'),primitives=mm,max_steps=20000)[0]['value']==want;cases+=1
    return dict(cases=cases,all_30_law_and_setup_binders_checked=True,physical_context_not_coordinate_point=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][239:243]:
        assert digest(u['text'].encode())==u['text_sha256'];ms=[math[n] for n in u['math_ids']]
        for m in ms:assert digest(m['mathml'].encode())==m['sha256']
        segments.append(dict(unit=u['id'],text=u['text'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],math=ms,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text']))))
    return dict(version='einstein-electron-rest-law-reading-v1',segments=segments,observations=['原刊917頁でu0240の設定指示と括弧内の命名、nur folgendes annehmenの限定とコロン、u0241の指定時点の静止と直後の時間部分、u0242の三行のμと二階微分とεX/Y/Z、u0243のwobeiと三座標・低速時のμの意味説明を続けて照合した。','初期運動を同じ座標時刻の右微分で読む。原文に固定長の時間粒やε–δの字面が印刷されているとはせず、有限時間の一定加速又は全時刻の静止へ替えない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,FACSIMILE,DOC)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    before=load_catalog(ROOT,PARENT_BASIS);after=load_catalog(ROOT,BASIS)
    assert after.document['statements'][:413]==before.document['statements'] and len(after.document['statements'])==415
    assert after.document['declarations'][:len(before.document['declarations'])]==before.document['declarations']
    assert all(after.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in before.entries.items())
    assert selection_binding(after,[412])==selection_binding(before,[412]);load_annotations(ROOT,BASIS,ANNOTATIONS)
    a=json.loads(read(ANNOTATIONS))['entries'];b=json.loads(read('data/point-particle-dynamics-identifiers-v1.json'))['entries'];assert a[:-4]==b
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    assert len(MEANINGS)==21 and len(PRIMITIVES)==16
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=21,new_general_relations=3,new_reference_constants=13,new_statements=2,all_413_prior_statements_and_meanings_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('future',future_checks),('content',content_checks),('premise',premise_checks),('presentation',presentation_checks),('binder',binder_checks),('structure',structure_checks)]}
    helpers=('compose_point_particle_dynamics','compose_limits','compose_material_relative_frame','compose_doppler_infinity','compose_relativity_conjecture','compose_two_postulates','check_point_particle_dynamics','check_attached_material_charge','check_material_acceleration','check_clock_site_time','check_rod_methods','check_ninth_section_opening','check_convective_foundation_reading','check_problem_series_reduction','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,*DEPENDENCIES,'scripts/compose_electron_rest_law_claim.py','scripts/check_electron_rest_law_claim.py','tests/test_electron_rest_law_claim.py',*(f'scripts/{n}.py' for n in helpers)}
    return dict(status='electron_rest_law_claim_connected_for_whole_unit_review',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
