"""Check the same clock's two time equalities, whole scope and consequence."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_origin_clock_equations import model,RECORDS
from scripts.compose_origin_clock_time import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/origin-clock-time-v1.md';SOURCE='data/einstein-origin-clock-time-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-origin-clock-equations-u0122-review-v1.json'
DEPENDENCIES=('reports/origin-clock-equations-v1.json','reports/origin-clock-question-v1.json')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zii':'equations','zij':'derived','zie':'clock','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b')));POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky','zzbb','zzbd'}|{'ejjl':{'ejjd','ejit'},'ejjm':{'ejjl'}}.get(name,set())
    if mode=='binding':bounds.add('svj')
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='joct'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='joctpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='joctpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'joctpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def time_checks():
    count=0
    for speed,t in product((-4,-3,0,3,4),(-7,Q(-1,3),0,Q(2,3),9)):
        cuts,m,coords,norm=model(speed,t);c=cuts.make;factor=Q(3,5) if abs(speed)==4 else Q(4,5) if abs(speed)==3 else Q(1)
        assert run('ejje',['x','y'],m) and run('svj',['x','y'],m);count+=2
        assert coords['y'][3]==factor*t==t-(1-factor)*t
        for wrong in (coords['y'][3]+1,coords['y'][3]-1):
            old=coords['y'][3];coords['y'][3]=wrong;assert not run('svj',['x','y'],m);coords['y'][3]=old;count+=1
        if speed and t:
            for wrong in (t/factor,(1-factor)*t,t):
                old=coords['y'][3];coords['y'][3]=wrong;assert not run('svj',['x','y'],m);coords['y'][3]=old;count+=1
        # Native source expression uses the same t in both the proportional
        # and the difference form. Negative t does not mean a negative duration.
        unknowns(lambda mm:run('svj',['x','y'],mm),m,('tc','zb7','sky','sje','zc5','zc6'))
    # Break the difference rewrite at its final subtraction only, retaining
    # the proportional equality. This checks that the second equality is read.
    cuts,m,coords,norm=model(3,5);r=cuts.read;c=cuts.make;sub=m['bf']
    bad=m|{'bf':lambda a,b:c(Q(99)) if (r(a),r(b))==(5,1) else sub(a,b)}
    assert not run('svj',['x','y'],bad);count+=1
    # Break the proportional product only, retaining the difference equality.
    mul=m['shv'];bad=m|{'shv':lambda a,b:c(Q(99)) if (r(a),r(b))==(Q(4,5),Q(5)) else mul(a,b)}
    assert not run('svj',['x','y'],bad);count+=1
    # Fault injection above tests both conjuncts, not a valid arithmetic model.
    for speed in (5,6):
        try:run('svj',['x','y'],m|{'zb7':lambda:c(Q(speed))})
        except ValueError:pass
        else:raise AssertionError('Singular or superluminal formula accepted')
        count+=1
    return dict(cases=count,native_proportional_and_difference_equalities=True,signed_coordinate_time_and_same_positive_factor=True,both_equalities_exercised_with_labeled_arithmetic_faults=True)

@lru_cache(None)
def scope_checks():
    count=0;domain=('a','b')
    for own,lab in product(domain,repeat=2):
        rows={'ejjd':{('a','context')},'ejit':{('a',own,lab,'context')},'svj':{(lab,own)}}
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejjl',['a','context'],mm,domain,'binding')
        assert check(mm);count+=1
        for n in ('ejjd','svj'):
            for row in rows[n]:
                assert not check(mm|{n:lambda *xs:False});count+=1
                for slot in range(len(row)):
                    bad=tuple('other' if i==slot else x for i,x in enumerate(row));assert not check(mm|{n:relation({bad})});count+=1
        for a,b in set(product(domain,repeat=2))-{(own,lab)}:
            assert not check(mm|{'ejit':relation(rows['ejit']|{('a',a,b,'context')})});count+=1
        unknowns(check,mm,rows)
    cuts,m,coords,norm=model();rows={'ejjd':{('x','context')},'ejit':{('x','y','x','context'),('x','time','z','context')}}
    mm=m|{n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejjl',['x','context'],mm,RECORDS)
    assert check(mm);count+=1
    for rec in RECORDS:
        coords[rec][3]+=1;assert not check(mm);coords[rec][3]-=1;count+=1
    assert not check(mm|{'ejjd':lambda *xs:False});count+=1
    assert not check(mm|{'ejit':relation(rows['ejit']|{('x','y','z','context')})});count+=1
    # The numeric claim does not introduce a new condition on the spatial
    # record fields; the unchanged full physical scope supplies that meaning.
    coords['x'][0]+=1;assert check(mm);count+=1
    assert not check(mm|{'ejjd':lambda *xs:False});count+=1
    return dict(cases=count,every_same_clock_pair_and_record_order=True,whole_current_physical_scope_required=True,native_time_formulas_on_all_selected_pairs=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (
        ('ejjm',{'ejjl':{('clock','context')}}),
        ('ejjn',{'zc':{('derived','author','ejjg','ejjm','section','discourse')}}),
        ('ejjp',{'eir3':{('derived','author','paper','ejjo','discourse')},'ue':{('equations','derived','discourse')}})):
        mm={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),mm,rows)
        if name!='ejjm':assert run(name,[],mm|{'ejjg':forbidden,'ejjm':forbidden,'ejjo':forbidden});count+=1
    return dict(cases=count,same_preceding_equations_and_derived_content=True,author_consequence_and_source_order_not_automatic_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    for u in inv['units'][122:124]:
        math=[]
        for mid in u['math_ids']:
            assert mid=='M0216';e=table[mid];root=ET.fromstring(e['mathml']);flat=re.sub(r'\s','',''.join(root.itertext()));assert flat=='τ=t1−(vV)2=t−(1−1−(vV)2)t,'
            ns='{http://www.w3.org/1998/Math/MathML}';assert len(root.findall('.//'+ns+'msqrt'))==2 and len(root.findall('.//'+ns+'mfrac'))==2
            assert [n.text for n in root.iter(ns+'mo')].count('=')==2
            math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math))
    assert [s['unit'] for s in segments]==['einstein-1905:u0123','einstein-1905:u0124']
    retrieval='artifacts/einstein-origin-clock-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-origin-clock-time-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904'],segments=segments,observations=['原刊904頁でx=vt.に続くEs ist also、次の二等号の表示、末尾のコンマとworaus folgtへの接続を通読した。','第一の右辺はtと正の平方根の積、第二の右辺はtから(1−同じ平方根)tを引く値である。βの逆数に相当する因子をβ自身に替えず、同じtを共有する。','表示の末尾はコンマで後続の遅れの説明へ続く。今回の二単位へ単位秒・二次近似の内容を入れない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==341
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[339])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();ds={d['name']:d for d in doc['declarations']};assert ds['ejjo']['body']['force']=='assert'
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    names={d['name'] for d in extract_document(doc,roots=['ejjm'],statement_indices=[]).document['declarations']}
    assert {'ejjd','ejit','ejip','ejir','eiyx','eiyy','svj','stw'}<=names and not {'zac','shd','svk','svl','ejiu'}&names
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=340,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('time',time_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_origin_clock_equations','check_coordinate_correspondence','check_moving_trip_geometry','check_clock_site_time','check_transverse_time','check_material_relative_frame','check_rod_methods','compose_origin_clock_equations','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_origin_clock_time.py','scripts/check_origin_clock_time.py','tests/test_origin_clock_time.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='origin_clock_proportional_time_and_difference_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0123–u0124の全体通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
