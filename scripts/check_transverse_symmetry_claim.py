"""Check physical-meaning attribution, symmetry scope and equivalent phi rewrite."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_four_coordinate_claim import model as numeric_model,RS
from scripts.check_transverse_comparison_scope import source_record as prior_source
from scripts.compose_transverse_symmetry_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,GROUPS,build

DOC='docs/transverse-symmetry-claim-v1.md';SOURCE='data/einstein-transverse-symmetry-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-endpoint-u0097-review-v1.json'
DEPENDENCIES=('reports/transverse-comparison-scope-v1.json','reports/transverse-measured-length-v1.json','reports/transverse-endpoint-claim-v1.json','reports/reciprocal-claim-v1.json')
CONSTANTS={'rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb6':'context','zg2':'other','zhj':'endpoints','zhk':'meaning','zhl':'symmetry','zhm':'reversal','eisn3':'fractions','zhn':'rewrite'}
DOMAIN=tuple(x for n,x in CONSTANTS.items() if n not in ('ri','zb6','zg2'));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}
    bounds|={'ejdk':{'ejcl','ejcm','ejcn'},'ejdl':{'ejc2'},'ejdn':{'ejde'},'ejdp':{'ejdh'},'ejdq':{'ejdn','ejdp'},'ejdr':{'ejdp'},'ejdt':{'ejdp'} if mode=='numeric' else {'ejdp','ejdi','ssk'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jtsc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jtscpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jtscpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert not slots
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m;mm.setdefault('jtscpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def truth(on):return Content(POINTS,(False,on,False))

@lru_cache(None)
def scope_checks():
    count=0
    for name,names in (('ejdk',('ejcl','ejcm','ejcn')),('ejdq',('ejdn','ejdp'))):
        for bits in product((False,True),repeat=len(names)):
            m={n:lambda on=on:truth(on) for n,on in zip(names,bits)}
            assert run(name,m)==all(bits);count+=1
    cuts,m=numbers();c=cuts.make;r=cuts.read;lengths={'context':Q(1),'other':Q(2)}
    m['zha']=lambda s:c(lengths[s]) if s in lengths else forbidden()
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    for name,bound,rows in (('ejdl','ejc2',{('context',Q(1))}),('ejdp','ejdh',{(Q(1),Q(2))})):
        base=m|{bound:lambda *xs,rows=rows:norm(xs) in rows}
        count+=perturb(lambda mm:run(name,mm),base,{bound:rows},norm)
        unknowns(lambda mm:run(name,mm),base,('zha',))
    for on in (False,True):assert run('ejdn',{'ejde':lambda:on})==on;count+=1
    for on in (False,True):
        for length in (Q(1),Q(2)):
            lengths['other']=length
            assert run('ejdr',m|{'ejdp':lambda:truth(on)})==(on and length==1);count+=1
    for premise,left,right in product((False,True),repeat=3):
        m={n:lambda on=on:truth(on) for n,on in zip(('ejdp','ejdi','ssk'),(premise,left,right))}
        assert run('ejdt',m)==(not premise or left==right);count+=1
    return dict(cases=count,same_current_endpoints_measurement_and_symmetry_premises=True,positive_and_negative_measurements_not_interchanged=True,or_is_conditional_biconditional_not_one_way_implication=True)

@lru_cache(None)
def numeric_checks():
    count=0
    for proper,plus,minus in product((Q(1),Q(3)),(Q(-2),Q(1,2),Q(2)),(Q(-2),Q(1,2),Q(2))):
        cuts,m,*_=numeric_model();c=cuts.make;r=cuts.read
        m|={'zgz':lambda:c(proper),'zeq':lambda:FunctionValue((RS,),RS,lambda s:c((plus if r(s)==3 else minus)/Q(5,4)) if r(s) in (3,-3) else forbidden()),'ejdp':lambda:truth(True)}
        assert run('ejdi',m)==(plus==minus);count+=1
        assert run('ssk',m)==(plus==minus);count+=1
        assert run('ejdt',m,'numeric');count+=1
    unknowns(lambda mm:run('ejdt',mm,'numeric'),m,('zeq','zgz','sje','sca'))
    return dict(cases=count,native_two_fractions_and_phi_values_equivalent_for_nonzero_values=True,negative_phi_and_nonunit_common_value_not_silently_removed=True)

@lru_cache(None)
def presentation_checks():
    count=0
    cases=(
      ('ejdm',{'zc':{('meaning','author','ejdk','ejdl','section','discourse')},'zhf':{('meaning','author','spc','ejdl','section','discourse')}}),
      ('ejdo',{'uh':{('symmetry','author','ejdn','section','discourse')},'eisn2':{('symmetry','author','ejdn','section','discourse')},'zdg':{('symmetry','author','ejdn','section','discourse')}}),
      ('ejds',{'zc':{('reversal','author','ejdq','ejdr','section','discourse')}}),
      ('ejdu',{'zc':{('fractions','author','ejdr','ejdi','section','discourse')}}),
      ('ejdv',{'zd3':{('rewrite','author','ejdp','ejdi','ssk','section','discourse')},'uh':{('rewrite','author','ejdt','section','discourse')}}),
    )
    for name,rows in cases:
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,mm),m,rows)
        assert run(name,m|{n:forbidden for n in ('ejdk','ejdl','ejdn','ejdq','ejdr','ejdp','ejdi','ejdt','ssk','spc')});count+=1
    for value,message,claim,node,previous in GROUPS:
        rows={'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}
        count+=perturb(lambda mm:run(claim,mm),{n:relation(rs) for n,rs in rows.items()},rows)
    return dict(cases=count,same_measured_length_gives_same_function_physical_meaning=True,spatial_symmetry_reason_assertion_and_obviousness_distinct=True,two_consequences_and_equivalent_rewrite_ordered=True,quoted_physics_not_executed_as_proof=True)

@lru_cache(None)
def source_record():
    old=prior_source();validate_hashes(ROOT,old['source_sha256'])
    pins={p:h for p,h in old['source_sha256'].items() if p!='docs/transverse-comparison-scope-v1.md'};pins[DOC]=digest((ROOT/DOC).read_bytes())
    return dict(version='einstein-transverse-symmetry-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['902'],segments=old['segments'],observations=['原刊902頁のDie Länge des Stabesから、物理的意味、対称性による明白さ、正負交換、Hieraus folgt、二分数の等値、oder、φの二値の等値と句点まで照合した。','Geschwindigkeitはこの対称性の比較では速度の大きさ。RichtungとSinnは方向と向きの両方を指すと読み、全非零光速未満ベクトルの理想化した比較群を明示した。','測定長は正の同時刻距離。l/φ(v)への一致が選ぶ向きの読みを明示し、先行端点式だけからφの正値を証明したことにしない。','同じ棒の全物質点・固有形状・尺度を保つ設定群であり、同速の場合の長さ不変を候補選択に入れない。','M0186はl/φ(v)=l/φ(−v)。oderは同じ正のlと非零φの下でM0187のφ(v)=φ(−v)へ書き換える。次のφ=1はまだ加えない。'],source_sha256=pins)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-5]==old.document['statements'] and len(new.document['statements'])==323
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[315,316,317])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'ejde','ejc6','ejdc','ejc2','ejdh','ejdf','ejdi','ssk','eiyx'}<=set(ds)
    assert not set(ds)&{'za','shd','zgj','ssd','ssc','ssl','ssm'}
    assert all(ds[g[1]]['body']['force']=='assert' for g in GROUPS)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=318,prior_whole_unit_judgment_preserved=True,current_complete_comparison_scope_and_measured_meaning=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('scope',scope_checks),('numeric',numeric_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_transverse_symmetry_claim.py','scripts/check_transverse_symmetry_claim.py','tests/test_transverse_symmetry_claim.py','scripts/check_transverse_comparison_scope.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    selections=(list(INDICES[:4]),[321],[322],[322])
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selections[i],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='measured_phi_meaning_symmetry_and_equivalent_signed_rewrite_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0101–u0104の全文通読判断と登録','u0105以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
