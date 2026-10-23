"""Check dimension witnesses, speed comparisons, contrast and author attribution."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_segment import DOMAIN as BODY_DOMAIN,refused,relations
from scripts.check_material_shape_dimensions import setup,SS
from scripts.check_final_transform_claim import final_model
from scripts.compose_directional_contraction_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build

DOC='docs/directional-contraction-claim-v1.md';SOURCE='data/einstein-directional-contraction-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-moving-ellipsoid-u0114-review-v1.json'
DEPENDENCIES=('reports/material-shape-dimensions-v1.json','reports/moving-ellipsoid-v1.json','reports/shape-contraction-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zh6':'dimensions','zh3':'sphere','zic':'speed_order','eisob':'transverse','eisoc':'axial','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*BODY_DOMAIN,*CONSTANTS.values())));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}|{'ejgp':{'ejgj','ejgl'},'ejgq':{'ejgl'},'ejgr':{'ejgq'},'ejgs':{'ejgq'},'ejgt':{'ejgp','ejgm','ejgr','ejgs'},'ejgu':{'ejgp','ejgr'},'ejgv':{'ejgp','ejgs'},'ejgw':{'ejgp','ejgq'},'ejgz':{'ejgb','ejeh'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        sort=SS if name in ('ejgt','ejgu','ejgv','ejgw') else RS
        assert len(expose(d,{'forall','exists'},only_sort=sort))=={'ejgp':3,'ejgq':3,'ejgy':3,'ejgt':1,'ejgu':1,'ejgv':1,'ejgw':1}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jdcc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jdccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jdccpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jdccpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def dimension_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();c=cuts.make;count=0
    rows={'ejgj':{norm(['body',shape,'context'])},'ejgl':{('body','k','context',Q(0),a,Q(w)) for a,w in zip(('x','y','z'),(5,2,1))}}
    mm=relations(m,rows,norm);args=['body',shape,'context',*[c(Q(n)) for n in (5,2,1)]]
    count+=perturb(lambda mm:run('ejgp',args,mm,'instance'),mm,rows,norm)
    refused(lambda:run('ejgp',args[:3],mm))
    # Run the real positive-root and scale expressions; only cut arithmetic and
    # the already checked physical width relation are boundary interpretations.
    cuts,m,*_=final_model();c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    m|={'eisls':lambda f,u,s:c(Q(-1 if f=='k' else 0)) if f in ('K','k') and (u,s)==('duration','context') else forbidden(),'eislt':lambda f,u,s:c(Q(2)) if f in ('K','k') and (u,s)==('duration','context') else forbidden()}
    for axis,proper,observed,expected in (('x',5,4,True),('x',5,Q(25,4),False),('x',5,5,False),('x',0,0,True),('x',-5,-4,False),('y',5,5,True),('z',2,2,True),('y',5,4,False),('z',2,Q(8,5),False),('time',5,5,False)):
        rows={'ejgl':{('body','k','context',Q(-1),axis,Q(proper)),('body','K','context',Q(1),axis,Q(observed))}}
        mm=relations(m,rows,norm);args=['body',axis,'context',c(Q(proper)),c(Q(1)),c(Q(observed))]
        assert run('ejgq',args,mm,'instance')==expected;count+=1
        if expected:count+=perturb(lambda mm:run('ejgq',args,mm,'instance'),mm,rows,norm)
    rows={'ejgl':{('body','k','context',Q(-1),'x',Q(5)),('body','K','context',Q(1),'x',Q(4))}}
    mm=relations(m,rows,norm)
    for t in (0,2):assert not run('ejgq',['body','x','context',c(Q(5)),c(Q(t)),c(Q(4))],mm,'instance');count+=1
    unknowns(lambda mm:run('ejgq',['body','x','context',c(Q(5)),c(Q(1)),c(Q(4))],mm,'instance'),mm,('ejgl','eisls','eislt','tc','zb7','sky','sje'))
    refused(lambda:run('ejgq',['body','x','context'],mm))
    for name,axes in (('ejgr',('y','z')),('ejgs',('x',))):
        rows={'ejgq':{('body',a,'context') for a in axes}};mm=relations({},rows,lambda xs:tuple(xs));count+=perturb(lambda mm:run(name,['body','context'],mm),mm,rows)
    return dict(cases=count,finite_rest_dimensions_and_each_observed_width_exist=True,ratio_rest_to_moving_not_reciprocal=True,strict_axial_shortening_and_two_unchanged_transverse_axes=True,zero_width_and_time_scope_distinguished=True,native_real_witness_domain_refused=True)

@lru_cache(None)
def speed_checks():
    cuts,m,*_=final_model();c=cuts.make;r=cuts.read;count=0
    for length,speed,other in product((-2,0,2,5),(0,3,4),(0,3,4)):
        assert run('ejgx',[c(Q(n)) for n in (5,length,speed,other)],m);count+=1
        assert run('ejgy',[c(Q(n)) for n in (length,speed,other)],m,'instance');count+=1
    # Preserve admissibility and alter only the two final length products.
    # Changing the shared square root also invalidates beta in the antecedent,
    # which correctly makes this implication vacuous instead of falsifying it.
    args=[c(Q(n)) for n in (5,2,3,4)];multiply=m['shv']
    for changed in (lambda factor:Q(2),lambda factor:Q(2)/factor):
        mm=m|{'shv':lambda a,b,changed=changed:c(changed(r(b))) if r(a)==2 and r(b) in (Q(3,5),Q(4,5)) else multiply(a,b)}
        assert not run('ejgx',args,mm);count+=1
    unknowns(lambda mm:run('ejgx',args,mm),m,('sje','sky','bg'))
    refused(lambda:run('ejgy',[],m))
    return dict(cases=count,same_positive_rest_width_under_two_admissible_speeds=True,native_factor_and_beta_definitions_used=True,ordering_not_acceleration_history=True,unbounded_speed_domain_refused=True)

@lru_cache(None)
def scope_checks():
    cuts,m,pos,members,fs,pop,fields,shape,norm,support=setup();count=0;domain=('a','b')
    for bits in product((False,True),repeat=8):
        populations=[{p for p,b in zip(domain,bits[i:i+2]) if b} for i in range(0,8,2)]
        mm={'ejgp':lambda b,s,c:b in populations[0] and norm([s])==norm([shape]) and c=='context','ejgm':lambda b,s,c:b in populations[1] and norm([s])==norm([shape]) and c=='context','ejgr':lambda b,c:b in populations[2] and c=='context','ejgs':lambda b,c:b in populations[3] and c=='context'}
        assert run('ejgt',[shape],mm,'instance',domain)==all(p not in populations[0] or all(p in z for z in populations[1:]) for p in domain);count+=1
        for name,index in (('ejgu',2),('ejgv',3)):
            assert run(name,[shape],mm,'instance',domain)==all(p not in populations[0] or p in populations[index] for p in domain);count+=1
    for axis in domain:
        for bits in product((False,True),repeat=4):
            qualifying={p for p,b in zip(domain,bits[:2]) if b};valid={p for p,b in zip(domain,bits[2:]) if b}
            mm={'ejgp':lambda b,s,c:b in qualifying and norm([s])==norm([shape]) and c=='context','ejgq':lambda b,a,c:b in valid and a==axis and c=='context'}
            assert run('ejgw',[axis,shape],mm,'instance',domain)==all(p not in qualifying or p in valid for p in domain);count+=1
    for name in ('ejgt','ejgu','ejgv'):refused(lambda:run(name,[],mm,domain=domain))
    return dict(cases=count,all_bodies_all_shapes_and_same_eligibility_on_both_sides=True,full_shape_and_dimension_existence_not_only_numeric_ratio=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for bits in product((False,True),repeat=2):
        mm={n:lambda b=b:Content(POINTS,(b,b,b)) for n,b in zip(('ejgb','ejeh'),bits)}
        assert run('ejgz',[],mm)==all(bits);count+=1
    rows={'zc':{('dimensions','author','ejgz','ejgt','section','discourse'),('speed_order','author','ejgt','ejgy','section','discourse')},'uh':{('transverse','author','ejgu','section','discourse'),('axial','author','ejgv','section','discourse')},'eisnp':{('dimensions','author','transverse','ejgu','axial','ejgv','ejgw','discourse')}}
    mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejg2',[],mm);count+=perturb(check,mm,rows)
    assert check(mm|{n:forbidden for n in ('ejgz','ejgt','ejgu','ejgv','ejgw','ejgy')});count+=1
    rows={'eir3':{('dimensions','author','paper','ejg3','discourse')},'ue':{('sphere','dimensions','discourse')}}
    mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejg4',[],mm);count+=perturb(check,mm,rows)
    assert check(mm|{'ejg3':forbidden,'ejg2':forbidden});count+=1
    return dict(cases=count,contrast_and_both_consequences_preserve_direction=True,common_axis_dimension_not_logical_contradiction=True,author_presentation_not_automatic_physical_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));unit=inv['units'][115];assert unit['id']=='einstein-1905:u0116';end=unit['text'].index(' Für ');assert end==270;text=unit['text'][:end]
    table={m['id']:m for m in inv['math']};math=[];expected=('Y','Z','X','1:1−(v/V)2','v')
    for n,flat in zip(range(201,206),expected):
        m=table[f'M{n:04d}'];root=ET.fromstring(m['mathml']);assert re.sub(r'\s','', ''.join(root.itertext()))==flat
        if n==204:assert len(root.findall('.//{http://www.w3.org/1998/Math/MathML}msqrt'))==1
        math.append(dict(id=m['id'],sha256=m['sha256'],mathml_flat=flat))
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-directional-contraction-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,end],text=text,source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',text)),math=math)],observations=['原刊903頁でWährend alsoから第一文末ist.まで、Y,Zの不変、球から任意形状への括弧内の一般化、Xの比1対平方根、速度比較を再読した。','1:√(1−(v/V)²)は静止時対運動時の寸法の順と読む。三軸の射影幅は実際の同じ物体から取り、原文の有限寸法を持つ対象という読みを明示する。','Währendは対照で、同じ時期に二事件が生じる時間関係ではない。erscheinenはKの同時刻座標からの記述と読む。','最初のalsoと括弧内のalso auchは先の球から同じ結果を任意形状へ拡張する帰結、最後のalsoは縮小比から同じ静止幅に対する速度比較へ進む帰結として保持する。','u0116の後二文、M0206、光速極限・超光速での適用限界・後続への予告は残る。第一文だけの接続から全単位完成にはしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==333
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[331])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'ejgp','ejgq','ejgm','ejgl','stw','suk','eisnp','zc'}<=set(ds)
    assert all(ds[n]['parameters']==[] and ds[n]['result']=='individual' for n in PRIMITIVES)
    generic=extract_document(doc,roots=['ejgt'],statement_indices=[]).document
    assert not {d['name'] for d in generic['declarations']}&{'eje5','ejf7','zhw','zhx','sua','sub','sue','shd','zhu'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),new_primitives_only_source_anchors=True,preserved_statements=332,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('dimension',dimension_checks),('speed',speed_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_directional_contraction_claim.py','scripts/check_directional_contraction_claim.py','tests/test_directional_contraction_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_transverse_segment.py','scripts/check_material_shape_dimensions.py','scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_shape_contraction.py','scripts/compose_material_shape_dimensions.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_limits.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='directional_dimensions_contrast_and_speed_order_first_sentence_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0116後二文の極限・適用限界・後続への予告','段落全体の通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
