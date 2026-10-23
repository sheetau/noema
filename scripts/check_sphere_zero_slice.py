"""Check the native zero slice, same-event pullback and author's rewrite."""
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
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_final_transform_claim import final_model
from scripts.compose_sphere_zero_slice import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/sphere-zero-slice-v1.md';SOURCE='data/einstein-sphere-zero-slice-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-sphere-setting-u0110-review-v1.json'
DEPENDENCIES=('reports/sphere-setting-v1.json','reports/solid-sphere-geometry-v1.json','reports/final-transform-claim-v1.json','reports/sphere-slice-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zhw':'body','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zh2':'slice','eisn6':'sphere','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b','other')));POINTS=('context','discourse','other')

@lru_cache(None)
def fixture(name):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sje','sjd','sky'}|{'ejfr':{'eiyx'},'ejfs':{'ejfr','ejfa'},'ejft':{'ejfr','ejfa','eiyx','ssz'},'ejfu':{'ejfr','ejfa','stf'},'ejfv':{'ejff','ejfh','ejeh'},'ejfw':{'ejft'},'ejfx':{'ejfu'}}.get(name,set())
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jszs'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jszspoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jszspoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jszspoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    count=0;endtimes=[]
    for point in ((4,0,0,0),(-4,0,0,0),(0,5,0,0),(0,0,-5,0),(0,0,0,0),(Q(16,5),0,0,0),(5,0,0,0),(7,0,0,1)):
        cuts,m,coords,scopes,result,seen=final_model(3,point);c=cuts.make;r=cuts.read;x,y,z,t=map(Q,point)
        expected=t==0 and x*x/Q(16,25)+y*y+z*z==25
        assert run('ssn',['x','y'],m);assert run('stf',['x',c(Q(5))],m)==expected;count+=2
        assert run('ssz',['y',c(Q(5))],m)==(Q(25,16)*(x-3*t)**2+y*y+z*z==25);count+=1
        if x in (-4,4) and y==z==t==0:
            endtimes.append(coords['y'][3]);assert coords['y'][3]!=0;count+=1
            saved=coords['y'][3];coords['y'][3]=Q(0);assert not run('ssn',['x','y'],m);count+=1;coords['y'][3]=saved
        if expected:
            for radius in (-5,0,4):assert not run('stf',['x',c(Q(radius))],m);count+=1
            unknowns(lambda mm:run('stf',['x',c(Q(5))],mm),m,('zc5','zc6','tc','zb7','sky','sje','sca'))
    assert sorted(endtimes)==[Q(-3,5),Q(3,5)]
    return dict(cases=count,native_final_equations_and_zero_slice_checked=True,outer_square_and_transverse_coordinates_preserved=True,K_simultaneous_endpoints_have_distinct_nonzero_k_times=True,later_surface_not_zero_slice=True)

@lru_cache(None)
def scope_checks():
    cuts,m=numbers();c=cuts.make;domain=('a','b');count=0
    base=m|{'ra':lambda:'a','rb':lambda:'b','zc7':lambda:'b','eisls':lambda *xs:c(Q(-1)),'eislt':lambda *xs:c(Q(1)),'eiyx':lambda e,r,f,s:(e,r,f,s)==('a','b','a','context')}
    for time,lo,hi in product((-2,-1,0,1,2),(-1,1),(0,1)):
        mm=base|{'zc6':lambda *xs:c(Q(time)),'eisls':lambda *xs:c(Q(lo)),'eislt':lambda *xs:c(Q(hi))}
        assert run('ejfr',['a','b','context'],mm,domain)==(lo<=time<=hi and time==0);count+=1
    check=lambda mm:run('ejfr',['a','b','context'],mm,domain)
    unknowns(check,base|{'zc6':lambda *xs:c(Q(0))},('eiyx','zc6','eisls','eislt','sca'))
    pairs=tuple(product(domain,repeat=2));criterion=FunctionValue(('individual',),dict(kind='function',parameters=['individual'],result='truth'),lambda e:FunctionValue(('individual',),'truth',lambda r:r=='a'))
    for selectedmask,surfacemask in product(range(16),repeat=2):
        selected={p for i,p in enumerate(pairs) if selectedmask>>i&1};surface={p for i,p in enumerate(pairs) if surfacemask>>i&1}
        mm={'ra':lambda:'a','ejfr':lambda e,r,s:s=='context' and (e,r) in selected,'ejfa':lambda b,e,r,f,s:(b,f,s)==('b','a','context') and (e,r) in surface}
        expected=bool(selected&surface) and all(((e,r) in surface)==(r=='a') for e,r in selected)
        assert run('ejfs',['b','context',criterion],mm,domain)==expected;count+=1
    return dict(cases=count,K_zero_and_own_interval_native=True,all_selected_records_both_directions_and_nonempty_surface=True,native_two_individual_quantifiers=True)

@lru_cache(None)
def binding_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;domain=('a','b');count=0
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={'ejfr':{('a','a','context')},'ejfa':{('b','a','a','a','context'),('b','a','b','b','context')},'eiyx':{('a','b','b','context')},'ssz':{('b',Q(5))}}
    def model(rows):return m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b','rb':lambda:'a','zc7':lambda:'a','eisls':lambda *xs:c(Q(-1)),'eislt':lambda *xs:c(Q(1)),'zc6':lambda rec,role:c(Q(3,5) if rec=='b' else Q(0))}
    mm=model(rows);check=lambda mm:run('ejft',['b',c(Q(5)),'context'],mm,domain)
    count+=perturb(check,mm,rows,norm)
    assert not check(mm|{'eiyx':lambda e,rec,f,s:(e,rec,f,s)==('b','b','b','context')});count+=1
    assert not check(mm|{'eislt':lambda *xs:c(Q(0))});count+=1
    unknowns(check,mm,('eisls','eislt','zc6'))
    # Replacing the expression must still pass the same event/record pair and
    # radius to the new formula; the native formula is checked separately.
    rows={'ejfr':{('a','a','context')},'ejfa':{('b','a','a','a','context')},'stf':{('a',Q(5))}}
    mm=model(rows);count+=perturb(lambda mm:run('ejfu',['b',c(Q(5)),'context'],mm,domain),mm,rows,norm)
    for bits in product((False,True),repeat=3):
        mm={n:lambda b=b:Content(POINTS,(b,b,b)) for n,b in zip(('ejff','ejfh','ejeh'),bits)}
        assert run('ejfv',[],mm)==all(bits);count+=1
    for name,bound in (('ejfw','ejft'),('ejfx','ejfu')):
        rows={bound:{('body',Q(5),'context')}};mm=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{'zhx':lambda:c(Q(5))}
        count+=perturb(lambda mm:run(name,[],mm),mm,rows,norm)
    return dict(cases=count,same_event_in_both_frames_not_equal_times=True,missing_counterpart_and_wrong_body_or_radius_rejected=True,original_sphere_and_final_current_equations_all_required=True)

@lru_cache(None)
def presentation_checks():
    count=0
    for name,rows in (('ejfy',{'zd3':{('slice','author','ejfv','ejfw','ejfx','section','discourse')}}),('ejf2',{'eir3':{('slice','author','paper','ejfz','discourse')},'ue':{('sphere','slice','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run(name,[],mm);count+=perturb(check,m,rows)
        assert check(m|{n:forbidden for n in ('ejfv','ejfw','ejfx','ejft','ejfu','ejff','ejfh','ejeh')});count+=1
    assert not run('ejf2',[],{'eir3':lambda *xs:True,'ue':lambda *xs:True,'zh2':lambda:'sphere'});count+=1
    return dict(cases=count,same_slice_in_rewrite_source_and_target=True,quoted_rewrite_not_executed_as_physical_proof=True,source_equation_precedes_K_slice=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0197':'x,y,z','M0198':'t=0','M0199':'x²/(√(1−(v/V)²))²+y²+z²=R².'}
    for n,flat in zip(readings,('x,y,z','t=0','x2(1−(vV)2)2+y2+z2=R2.')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    ns={'m':'http://www.w3.org/1998/Math/MathML'};eq=ET.fromstring(math['M0199']['mathml']);frac=eq.find('.//m:mfrac',ns)
    assert len(eq.findall('.//m:mfrac',ns))==2 and len(eq.findall('.//m:msqrt',ns))==1
    denominator=list(frac)[1];power=denominator.find('m:msup',ns);assert power is not None and ''.join(list(power)[1].itertext())=='2' and list(power)[0].find('.//m:msqrt',ns) is not None
    for number in (112,113):
        u=inv['units'][number-1];assert u['id']==f'einstein-1905:u{number:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    retrieval='artifacts/einstein-sphere-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']})
    paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-sphere-zero-slice-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['903'],segments=segments,observations=['原刊903頁の元のξ,η,ζの球面式に続くDie Gleichung dieser OberflächeからKの零時刻の式まで通読した。dieserは同じ表面を参照し、x,y,zとt=0を同じ表示へ結ぶ。','M0199の分母全体の外に二乗があり、根号内は1−(v/V)²である。横二成分はy²+z²、右辺は同じR²、句点はMathML内に含まれる。','比較元も同じKの零断面の出来事にそろえる。k側の時刻τは一般に位置ごとに異なり、零へ固定しない。両系の対象期間はこの断面の表面記録を含む範囲として読む。','後続の回転楕円体・三半軸はu0114–u0115の帰結であり、今回の二単位に補って完成扱いしない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==331
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[327,328,329])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE));names={d['name'] for d in doc['declarations']}
    assert {'ejfa','eje7','eiyx','eiyy','ejeh','ssn','ssz','stf','sky'}<=names
    assert not names&{'shd','zhu','zhv','stl','stm'}
    assert next(d for d in doc['declarations'] if d['name']=='ejfz')['body']['force']=='assert'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=330,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('scope',scope_checks),('binding',binding_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_sphere_zero_slice.py','scripts/check_sphere_zero_slice.py','tests/test_sphere_zero_slice.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_clock_site_time.py','scripts/check_final_transform_claim.py','scripts/check_four_coordinate_claim.py','scripts/check_material_relative_frame.py','scripts/compose_limits.py','scripts/compose_rod_methods.py','scripts/compose_solid_sphere_geometry.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='same_material_surface_on_K_zero_time_slice_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0112–u0113の全文判断と登録','u0114以降の回転楕円体・半軸'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
