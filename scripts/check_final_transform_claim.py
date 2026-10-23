"""Check the signed branch, final equation scope, and author presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_four_coordinate_claim import model as numeric_model,RS,matches,numeric_sequence,RECORDS
from scripts.compose_final_transform_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,PRIMITIVES,GROUPS,build

DOC='docs/final-transform-claim-v1.md';SOURCE='data/einstein-final-transform-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-symmetry-u0101-review-v1.json'
DEPENDENCIES=('reports/transverse-symmetry-claim-v1.json','reports/transverse-measured-length-v1.json','reports/reciprocal-claim-v1.json','reports/four-coordinate-claim-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zb6':'context','zgu':'rod','zgv':'low','zgw':'high','ra':'K','zhn':'previous','zho':'unit','zhp':'final','zhq':'annotation','eisn4':'beta'}
DOMAIN=tuple(x for n,x in CONSTANTS.items() if n not in ('ri','zb6'));POINTS=('context','discourse','other')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','eiyz','eiy2','eiyy'}
    bounds|={'ejeh':{'eiy4'},'ejei':{'ei7c','ejeb','spq'},'ejdl':{'ejcf','ejcj','ejcz'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jftc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jftcpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jftcpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jftcapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jftcapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jftcpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def capture(name,m):
    out=[];assert run(name,[],m|{'jftcapture':lambda value:out.append(value) is None});assert len(out)==1;return out[0]

@lru_cache(None)
def branch_checks():
    count=0
    for plus,minus in product((Q(-2),Q(-1),Q(1,2),Q(1),Q(2)),repeat=2):
        cuts,m,*_=numeric_model();c=cuts.make;r=cuts.read
        m['zeq']=lambda:FunctionValue((RS,),RS,lambda s:c((plus if r(s)==3 else minus)/Q(5,4)) if r(s) in (3,-3) else forbidden())
        expected={'ejea':plus==minus and plus*minus==1,'ejeb':plus==1,'ejec':plus>0,'ejed':plus==minus and plus*minus==1 and plus>0}
        for name,value in expected.items():assert run(name,[],m)==value,(name,plus,minus);count+=1
        if plus==minus==-1:assert run('ejea',[],m) and not run('ejeb',[],m);count+=1
        unknowns(lambda mm:run('ejed',[],mm),m,('zeq','zb7','tc','sky','sca','bg'))
    # Retain the native current measurement-to-signed-quotient conjunction.
    # Its geometric/history boundaries were independently checked in the
    # pinned measured-length evidence; this boundary tests the actual arguments.
    for proper,length,plus in product((Q(1),Q(3)),(Q(-1),Q(1),Q(2)),(Q(-1),Q(1),Q(2))):
        cuts,m,*_=numeric_model();c=cuts.make;r=cuts.read
        m|={'zgz':lambda:c(proper),'zha':lambda ctx:c(length) if ctx=='context' else forbidden(),'zeq':lambda:FunctionValue((RS,),RS,lambda s:c(plus/Q(5,4)))}
        norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
        m|={'ejcf':lambda ctx:ctx=='context','ejcj':lambda *xs:norm(xs) in {('rod','low',Q(0),'context'),('rod','high',proper,'context')},'ejcz':lambda *xs:norm(xs)==('rod','low','high','K','context',length) and length>0}
        expected=length>0 and length==proper/plus
        assert run('ejdl',[],m)==expected;count+=1
        if expected:
            assert run('ejec',[],m);count+=1
            for n in ('ejcf','ejcj','ejcz'):assert not run('ejdl',[],m|{n:lambda *xs:False});count+=1
            unknowns(lambda mm:run('ejdl',[],mm),m,('zha','zgz','zeq','ejcz','sca'))
    for bits in product((False,True),repeat=3):
        m={n:lambda b=b:Content(POINTS,(b,b,b)) for n,b in zip(('ei7c','ejeb','spq'),bits)}
        assert run('ejei',[],m)==all(bits);count+=1
    return dict(cases=count,negative_common_unit_is_counterexample_to_two_relations_alone=True,positive_branch_is_separate_sufficient_condition=True,current_measured_length_quotient_and_argument_connection_checked=True,native_geometry_is_in_separate_pinned_evidence=True)

def final_model(speed=Q(3),point=(7,11,13,2)):
    beta={Q(0):Q(1),Q(3):Q(5,4),Q(4):Q(5,3)}[Q(speed)]
    cuts,m,coords,scopes,result,seen=numeric_model(speed,1/beta,point)
    # numeric_model's normalized phi is now exactly 1, while the original
    # coefficient is 1/beta. No redefinition of spc is made.
    return cuts,m,coords,scopes,result,seen

@lru_cache(None)
def equation_checks():
    count=0
    for speed,point in ((3,(7,11,13,2)),(4,(-2,3,7,5)),(0,(1,2,3,4))):
        cuts,m,coords,scopes,result,seen=final_model(speed,point)
        assert run('ejeb',[],m);count+=1
        for name in ('ssn','spg'):
            assert run(name,['x','y'],m);count+=1
            for slot in range(4):
                coords['y'][slot]+=1;assert not run(name,['x','y'],m);coords['y'][slot]-=1;count+=1
        for name in ('ejeg','ei7a'):
            seq=capture(name,m);assert matches(seq,coords,result);count+=1
            for record in ('x','y'):
                for slot in range(4):
                    coords[record][slot]+=1;assert matches(capture(name,m),coords,result);coords[record][slot]-=1;count+=1
            assert not matches(SequenceValue(tuple(reversed(seq.items)),seq.element_type),coords,result);count+=1
        unknowns(lambda mm:run('ssn',['x','y'],mm),m,('tc','zb7','sky','sje','zc6','zc5'))
    cuts,m,coords,scopes,result,seen=final_model();c=cuts.make;r=cuts.read
    element=next(d['result']['element'] for d in core_document()['declarations'] if d['name']=='ejeg')
    actual=numeric_sequence(cuts,coords,result,element)
    assert run('eiy4',[actual],m,domain=RECORDS);count+=1
    for slot in range(4):
        old=coords['time'][:];coords['time'][:]=coords['y'][:];coords['time'][[3,0,1,2][slot]]+=1
        bad=SequenceValue(actual.items[:slot]+actual.items[slot+1:],actual.element_type)
        assert not run('eiy4',[bad],m,domain=RECORDS);count+=1;coords['time'][:]=old
    assert not run('eiy4',[SequenceValue((),actual.element_type)],m,domain=RECORDS);count+=1
    # The final four forms themselves do not read the now-eliminated phi.
    assert run('ssn',['x','y'],m|{'zeq':forbidden});count+=1
    assert matches(capture('ejeg',m|{'zeq':forbidden}),coords,result);count+=1
    assert run('spq',[],m);count+=1
    unknowns(lambda mm:run('spq',[],mm),m,('tc','zb7','sky','sjd','sje','sca'))
    for beta in (Q(-5,4),Q(3,5),Q(9,4)):
        assert not run('spa',[c(Q(5)),c(Q(3)),c(beta)],m);count+=1
    return dict(cases=count,final_four_outputs_and_both_sequence_sides_checked=True,existing_phi_forms_agree_at_phi_one_without_renormalization=True,all_four_omissions_rejected_on_distinguishing_output=True,beta_same_positive_reciprocal_root=True,sequence_cut_boundary_not_general_real_proof=True)

@lru_cache(None)
def scope_checks():
    cuts,m,coords,scopes,result,seen=final_model();count=0
    m['eiy4']=lambda seq:matches(seq,coords,result)
    for label in ('baseline','omit_alias','spurious_relation','omit_source_pair','empty_left','extra_unmatched_left','different_value_alias'):
        scopes['left']={'x'};scopes['right']={'y','z','time'};scopes['pairs']={('x','y'),('x','z')};old=coords['z'][:]
        if label=='omit_alias':scopes['pairs'].remove(('x','z'))
        if label=='spurious_relation':scopes['pairs'].add(('x','time'))
        if label=='omit_source_pair':scopes['pairs']=set()
        if label=='empty_left':scopes['left']=set()
        if label=='extra_unmatched_left':scopes['left'].add('z')
        if label=='different_value_alias':coords['z']=[v+2 for v in old];scopes['pairs'].remove(('x','z'))
        assert run('ejeh',[],m,domain=RECORDS)==(label in ('baseline','different_value_alias')),label;count+=1
        coords['z'][:]=old
    scopes['left']={'x'};scopes['right']={'y','z','time'};scopes['pairs']={('x','y'),('x','z')}
    assert not run('ejeh',[],m|{'eiy4':lambda seq:False},domain=RECORDS);count+=1
    unknowns(lambda mm:run('ejeh',[],mm,domain=RECORDS),m,('eiyz','eiy2','eiyy','eiy4','zc6','zc5','sky','sje'))
    return dict(cases=count,current_nonempty_exact_correspondence_required=True,same_value_distinct_records_preserved=True,missing_and_extra_pairs_rejected=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ejee',{'zfl':{('annotation','author','ejdl','ejec','section','discourse')}}),('ejef',{'zc':{('unit','author','ejea','ejeb','section','discourse')}}),('ejej',{'zd3':{('final','author','ejei','ei7c','ejeh','section','discourse')}}),('ejek',{'uh':{('beta','author','spq','section','discourse')}})]
    for value,message,claim,node,previous in GROUPS:
        rs={'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}
        if claim=='ejem':rs['zfl']={('annotation','author','ejdl','ejec','section','discourse')}
        rows.append((claim,rs))
    count=0
    for name,rs in rows:
        m={n:relation(values) for n,values in rs.items()};count+=perturb(lambda mm:run(name,[],mm),m,rs)
        assert run(name,[],m|{n:forbidden for n in ('ejea','ejeb','ejec','ejed','ejdl','ei7c','ejei','ejeh','spq')});count+=1
    return dict(cases=count,quoted_two_relations_not_silently_strengthened=True,positive_branch_annotation_outside_author_message=True,consequence_rewrite_and_beta_have_distinct_ordered_nodes=True,quoted_contents_not_executed_as_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0188':'φ(v)=1','M0189':'τ=β(t−vx/V²); ξ=β(x−vt); η=y; ζ=z','M0190':'β=1/√(1−(v/V)²)'}
    expected=('φ(v)=1','τ=β(t−vV2x),ξ=β(x−vt),η=y,ζ=z,','β=11−(vV)2.')
    for n,flat in zip(readings,expected):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    ns={'m':'http://www.w3.org/1998/Math/MathML'};eq=ET.fromstring(math['M0189']['mathml']);beta=ET.fromstring(math['M0190']['mathml'])
    assert len(eq.findall('.//m:mtr',ns))==4 and len(eq.findall('.//m:mfrac',ns))==1
    assert len(beta.findall('.//m:mfrac',ns))==2 and len(beta.findall('.//m:msqrt',ns))==1
    for i,u in enumerate(inv['units'][104:108]):
        assert u['id']==f'einstein-1905:u{105+i:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    retrieval='artifacts/einstein-reciprocal-claim-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']})
    paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-final-transform-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['902'],segments=segments,observations=['原刊902頁のAus dieserからφ(v)=1、so daß、最終四式、wobei、β表示まで前後と合わせて通読した。','dieserは直前の同じφの正負値の一致、vorhin gefundenen Relationは前の積1。原文は正値の第三前提をここで列挙していない。','sein mußは二関係から必要な帰結であるという著者の推論。二関係だけでは−1も残るので、前段の測定長による正の枝の読みを発話外の注記として明示する。','四式の順はτ,ξ,η,ζ。時間式はβ(t−(v/V²)x)、縦式はβ(x−vt)、横式はy,zで、φや横式のβは残らない。','wobeiは同じ四式のβを正の1/√(1−(v/V)²)で指定する。原刊のβ式末尾はコンマ、固定MathMLは句点。この句読点差は数式内容を変えない。','後続は§4の剛体と時計に関する物理的意味の考察であり、今回の4単位へ取り込まない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-3]==old.document['statements'] and len(new.document['statements'])==326
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[318,319,320,321])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[g[1]]['body']['force']=='assert' for g in GROUPS)
    assert 'zfl' not in extract_document(doc,roots=['ejel'],statement_indices=[]).retained_symbols
    assert 'zfl' in extract_document(doc,roots=['ejem'],statement_indices=[]).retained_symbols
    names=set(extract_document(doc,roots=['ejeh'],statement_indices=[]).retained_symbols)
    assert {'ei7l','eiy4','eiyz','eiy2','eiyy','ssn'}<=names
    assert not names&{'spi','spk','sso','ssp','shd','ssl'}
    assert set(extract_document(doc,roots=['ejea'],statement_indices=[]).retained_symbols).isdisjoint({'ejec','ejdl','ssm','ejed'})
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=323,prior_whole_unit_judgment_preserved=True,current_scope_not_legacy_record_binding=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('branch',branch_checks),('equations',equation_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_final_transform_claim.py','scripts/check_final_transform_claim.py','tests/test_final_transform_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_four_coordinate_claim.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py','scripts/compose_coordinate_correspondence.py'}
    selections=([323,324],[324],[324,325],[325])
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=selections[i],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='phi_one_final_current_transformation_and_beta_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,general_real_physical_derivation_proved=False,remaining=['u0105–u0108の全文通読判断と登録','u0109以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
