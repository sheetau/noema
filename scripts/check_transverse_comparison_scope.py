"""Check intrinsic rod matching, unfiltered comparisons and signed phi values."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_material_relative_frame import RS,FS
from scripts.check_translated_light_trial import expose
from scripts.check_transverse_measured_length import model as physical_model,source_record as prior_source
from scripts.check_transverse_segment import DOMAIN,refused,relations
from scripts.check_four_coordinate_claim import model as numeric_model
from scripts.compose_transverse_comparison_scope import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/transverse-comparison-scope-v1.md';SOURCE='data/einstein-transverse-comparison-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-endpoint-u0097-review-v1.json'
DEPENDENCIES=('reports/transverse-measured-length-v1.json','reports/transverse-endpoint-claim-v1.json','reports/rigid-body-kinematics-v1.json','reports/first-principle-v1.json')
CONSTANTS={'ra':'K','zbm':'k','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zgu':'body','zgv':'low','zgw':'high','zb6':'context','zg2':'other'}
POINTS=('context','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    bounds|={'ejc6':{'eiad'},'ejda':{'ejcc','ejc5','eioj','ejc6'},'ejdb':{'ejda'},'ejdc':{'ejdb'},'ejdd':{'ejda'},'ejde':{'ejda','ejdc','ejdd'},'ejdf':{'ejci','ejcg','srw','sry'},'ejdg':{'ejdb','ejcc','ejdf'},'ejdh':{'ejdg'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':assert len(expose(d,{'forall','exists'},only_sort=RS))=={'ejdc':4,'ejde':3}[name]
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtcs'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtcspoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtcspoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jtcspoint',lambda:'context')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=900000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def setup_shapes():
    cuts,m,pos,members,fs,restfs,pop,fields,norm,vel,drift=physical_model();c=cuts.make;r=cuts.read
    populations={'context':members.copy(),'other':members.copy()}
    positions={'context':{p:xyz.copy() for p,xyz in pos.items()},'other':{p:[xyz[1]+7,-xyz[0]+5,xyz[2]-3] for p,xyz in pos.items()}}
    families={s:[FunctionValue(('individual',),FS,lambda p,s=s,a=a:FunctionValue((RS,),RS,lambda t:c(positions[s][p][a]))) for a in range(3)] for s in POINTS}
    starts={'context':Q(0),'other':Q(3)};ends={'context':Q(2),'other':Q(5)}
    def family(b,f,lu,tu,role,s):
        if (b,f,lu,tu)!=('body','k','length','duration') or role not in ('x','y','z') or s not in POINTS:forbidden()
        return families[s][('x','y','z').index(role)]
    m|={'eislu':family,'eirh':lambda b,p,s:b=='body' and s in populations and p in populations[s],'eisls':lambda f,u,s:c(starts[s]) if (f,u)==('k','duration') and s in starts else forbidden(),'eislt':lambda f,u,s:c(ends[s]) if (f,u)==('k','duration') and s in ends else forbidden()}
    def rows():
        histories=[]
        for s in POINTS:
            member=FunctionValue(('individual',),'truth',lambda p,s=s:p in populations[s])
            histories.append(norm(['body','k',s,'length','duration',c(starts[s]),c(ends[s]),member,*families[s]]))
        return {'eiad':set(histories),'eisdd':{('k','length','duration',s) for s in POINTS}}
    return cuts,m,positions,populations,starts,ends,norm,rows

@lru_cache(None)
def shape_checks():
    cuts,m,pos,pop,starts,ends,norm,rows=setup_shapes();c=cuts.make;count=0
    check=lambda mm:run('ejc6',['body','k','context','other'],mm)
    count+=perturb(check,relations(m,rows(),norm),rows(),norm)
    for p in ('p','q','r'):
        pop['other'].remove(p);assert not check(relations(m,rows(),norm));count+=1;pop['other'].add(p)
    pop['other'].add('other');assert not check(relations(m,rows(),norm));count+=1;pop['other'].remove('other')
    # End positions stay fixed while a material point changes intrinsic position.
    for p,a in product(('p','q','r'),range(3)):
        pos['other'][p][a]+=1;assert not check(relations(m,rows(),norm));count+=1;pos['other'][p][a]-=1
    starts['other']=Q(9);ends['other']=Q(11);assert check(relations(m,rows(),norm));count+=1
    ends['other']=starts['other'];assert not check(relations(m,rows(),norm));count+=1;ends['other']=Q(11)
    base=relations(m,rows(),norm);unknowns(check,base,('eislu','eirh','eisls','eislt'))
    return dict(cases=count,native_complete_membership_and_all_intrinsic_pair_distances=True,translated_rotated_and_different_clock_origins_allowed=True,same_end_length_cannot_hide_changed_material_or_internal_shape=True)

def speed_model():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    speeds={'context':[Q(3),Q(0),Q(4)],'other':[Q(-4),Q(3),Q(0)]}
    m|={'tc':lambda:c(Q(10)),'zgz':lambda:c(Q(2)),'eislc':lambda a,b,lu,tu,axis,s:c(speeds[s][('x','y','z').index(axis)]) if (a,b,lu,tu)==('K','k','length','duration') and axis in ('x','y','z') and s in speeds else forbidden()}
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    return cuts,m,speeds,norm

@lru_cache(None)
def eligibility_checks():
    cuts,m,speeds,norm=speed_model();c=cuts.make;count=0
    rows={'ejcc':{('body','low','high','context',Q(2))},'ejc5':{('body','low','high','K','other','k',Q(2),*speeds['other'],Q(7))},'eioj':{('K','k','length','duration','other')},'ejc6':{('body','k','context','other')}}
    m=relations(m,rows,norm);check=lambda mm:run('ejda',['other',c(Q(7))],mm)
    count+=perturb(check,m,rows,norm)
    for velocity in ((0,0,0),(10,0,0),(11,0,0)):
        speeds['other']=list(map(Q,velocity));assert not check(m|{'ejc5':lambda *xs:True});count+=1
    speeds['other']=[Q(-4),Q(3),Q(0)]
    # Distinct measured values are eligible; equal length is not a filter.
    for length in (1,7,9):
        rs={'ejc5':{('body','low','high','K','other','k',Q(2),*speeds['other'],Q(length))}}
        assert run('ejda',['other',c(Q(length))],relations(m,rs,norm));count+=1
    rows={'ejda':{('other',Q(7))}};base=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejdb',['other',*[c(x) for x in speeds['other']],c(Q(7))],mm),base,rows,norm)
    for a in range(3):
        wrong=speeds['other'].copy();wrong[a]+=1;assert not run('ejdb',['other',*[c(x) for x in wrong],c(Q(7))],base);count+=1
    rows={'ejda':{('context',Q(1)),('other',Q(7))}};base=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejdd',['context',c(Q(1)),'other',c(Q(7))],mm),base,rows,norm)
    speeds['other'][2]=Q(1);assert not run('ejdd',['context',c(Q(1)),'other',c(Q(7))],base);count+=1
    return dict(cases=count,same_rod_full_frame_velocity_and_measured_length_bound=True,unequal_lengths_not_filtered_from_comparison=True,same_speed_uses_all_three_signed_components=True)

@lru_cache(None)
def range_checks():
    cuts,m,speeds,norm=speed_model();c=cuts.make;count=0
    vectors=((3,0,0),(-3,0,0),(0,3,0),(0,0,-3),(3,4,0),(Q(3,2),0,Q(-3,2)))
    for vector in vectors:
        target=('other',*map(Q,vector),Q(7));base=m|{'ejdb':lambda *xs,target=target:norm(xs)==target}
        args=[*[c(Q(x)) for x in vector],c(Q(7))]
        assert run('ejdc',args,base,'instance');count+=1
        assert not run('ejdc',args,base|{'ejdb':lambda *xs:False},'instance');count+=1
        for i in range(5):
            wrong=tuple('wrong' if j==i else x for j,x in enumerate(target))
            assert not run('ejdc',args,base|{'ejdb':lambda *xs,wrong=wrong:norm(xs)==wrong},'instance');count+=1
    for vector in ((0,0,0),(10,0,0),(11,0,0)):
        assert run('ejdc',[*[c(Q(x)) for x in vector],c(Q(7))],m|{'ejdb':lambda *xs:False},'instance');count+=1
    refused(lambda:run('ejdc',[],base))
    # Real-length quantifiers are exposed; situation quantifiers stay native.
    values={'context':Q(1),'other':Q(1)}
    base=m|{'ejda':lambda s,length:s in values and cuts.read(length)==values[s],'ejdc':lambda:True,'ejdd':lambda first,a,second,b:first in values and second in values and cuts.read(a)==values[first] and cuts.read(b)==values[second]}
    assert run('ejde',[c(Q(1)),c(Q(1)),c(Q(1))],base,'instance');count+=1
    for missing in ('ejda','ejdc'):
        assert not run('ejde',[c(Q(1)),c(Q(1)),c(Q(1))],base|{missing:lambda *xs:False},'instance');count+=1
    values['other']=Q(7)
    assert not run('ejde',[c(Q(1)),c(Q(1)),c(Q(7))],base,'instance');count+=1
    assert not run('ejde',[c(Q(1)),c(Q(7)),c(Q(1))],base,'instance');count+=1
    refused(lambda:run('ejde',[],base))
    return dict(cases=count,all_directions_require_a_current_physical_setting=True,complete_range_and_anchor_nonvacuous=True,native_situation_pairs_reject_unequal_same_speed_lengths=True,native_real_range_refused=True)

@lru_cache(None)
def signed_checks():
    count=0;small=('a','b')
    for speed in (Q(3),Q(-3)):
        cuts,m,*_=numeric_model(scale=Q(8,5));c=cuts.make;r=cuts.read
        m['zeq']=lambda:FunctionValue((RS,),RS,lambda s:c(Q(8,5) if r(s)==3 else Q(12,5)) if r(s) in (3,-3) else forbidden())
        phi=Q(2 if speed==3 else 3)
        for row in product(small,repeat=3):
            base=m|{'ejci':lambda *xs:xs==('a','b','context'),'ejcg':lambda b,p,e,kr,mr,s,row=row:(b,p,e,kr,mr,s)==('a','b',*row,'context'),'srw':lambda kr,mr,v,l,row=row:(kr,mr,r(v),r(l))==(*row[1:],speed,Q(2)),'sry':lambda kr,v,l,p,row=row:(kr,r(v),r(l),r(p))==(row[1],speed,Q(2),phi)}
            args=['a','b',c(Q(2)),c(speed),'context']
            assert run('ejdf',args,base,domain=small);count+=1
            for missing in ('ejci','srw','sry'):
                assert not run('ejdf',args,base|{missing:lambda *xs:False},domain=small);count+=1
    cuts,m,*_=numeric_model(scale=Q(8,5));c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    m|={'zgz':lambda:c(Q(2))}
    rows={'ejdb':{('other',Q(-3),Q(0),Q(0),Q(1))},'ejcc':{('body','low','high','other',Q(2))},'ejdf':{('body','low',Q(0),Q(-3),'other'),('body','high',Q(2),Q(-3),'other')}}
    m=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejdg',['other',c(Q(-3)),c(Q(1))],mm),m,rows,norm)
    rows={'ejdg':{('context',Q(3),Q(1)),('other',Q(-3),Q(2))}};m=relations(m,rows,norm)
    count+=perturb(lambda mm:run('ejdh',[c(Q(1)),c(Q(2))],mm),m,rows,norm)
    assert not run('ejdh',[c(Q(1)),c(Q(2))],m|{'zg2':lambda:'context'});count+=1
    # Native fractions can be equal with negative phi; no phi=1 is asserted.
    for plus,minus in ((2,2),(2,3),(-2,-2),(-2,2),(Q(1,2),Q(1,2))):
        cuts,m,*_=numeric_model();c=cuts.make;r=cuts.read
        m|={'zgz':lambda:c(Q(2)),'zeq':lambda:FunctionValue((RS,),RS,lambda s:c(Q(plus if r(s)==3 else minus)/Q(5,4)) if r(s) in (3,-3) else forbidden())}
        assert run('ejdi',[],m)==(plus==minus);count+=1
        unknowns(lambda mm:run('ejdi',[],mm),m,('zeq','zgz','sje','sca'))
    return dict(cases=count,negative_speed_uses_same_phi_at_negative_argument=True,full_record_scope_and_both_signed_measurements=True,native_two_fraction_equality_not_phi_one=True)

@lru_cache(None)
def source_record():
    old=prior_source();validate_hashes(ROOT,old['source_sha256'])
    pins={p:h for p,h in old['source_sha256'].items() if p!='docs/transverse-measured-length-v1.md'};pins[DOC]=digest((ROOT/DOC).read_bytes())
    return dict(version='einstein-transverse-comparison-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=old['pages'],segments=old['segments'],observations=['同じ特定の棒を全物質点と固有系の全点対距離の一致として保つ。','速度の大きさだけへの依存を同速設定の測定長の不変性として構成し、候補条件に長さの一致を入れない。','方向一般は0<|v⃗|<Vの全三成分についての比較設定の存在という理想化を明示し、反転二例へ縮めない。','正負設定は同じK/k・棒・尺度のまま速度だけを反転し、同じφの正負引数を区別する。','M0186は二つの分数の等値。著者の対称性の理由・明白さ・帰結とoderの提示、全文判断は未追加。'],source_sha256=pins)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==318
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[315,316,317])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'eioj','eislc','ejc5','ejcz','ejcg','eiyx','eigw'}<=names
    assert not names&{'zhc','zha','za','shd','zgj','ssd','ssc','ssl'}
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=318,prior_whole_unit_judgment_preserved=True,no_equal_length_filter_or_opaque_setting_selector=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('shape',shape_checks),('eligibility',eligibility_checks),('range',range_checks),('signed',signed_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_comparison_scope.py','scripts/check_transverse_comparison_scope.py','tests/test_transverse_comparison_scope.py','scripts/check_transverse_measured_length.py','scripts/check_transverse_segment.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_material_relative_frame.py','scripts/check_translated_light_trial.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py'}
    return dict(status='same_intrinsic_rod_complete_direction_scope_and_signed_comparisons_checked',document=FULL,**results,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['測定長による同じφの物理的意味の提示','方向不変性の対称性による理由と明白さの著者帰属','正負速度の長さ不変から二分数の等値、oderのφの等値への提示','u0101–u0104の本文接続・通読判断・登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
