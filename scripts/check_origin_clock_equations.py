"""Check both native equations and their shared current-clock scope."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
from xml.etree import ElementTree as ET
import json,re
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import Content,FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_transverse_time import square_root
from scripts.compose_origin_clock_equations import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,build

DOC='docs/origin-clock-equations-v1.md';SOURCE='data/einstein-origin-clock-equations-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-origin-clock-u0118-review-v1.json'
DEPENDENCIES=('reports/origin-clock-question-v1.json','reports/final-transform-claim-v1.json','reports/event-coordinate-task-v1.json')
CONSTANTS={'ra':'K','zbm':'k','ta':'length','rb':'duration','yn':'x','yo':'y','yp':'z','zc7':'time','zb6':'context','rd':'author','eirf':'paper','eisn5':'section','zig':'question','zii':'equations','zie':'clock','ri':'discourse'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'a','b')));POINTS=('context','discourse','other');RECORDS=('x','y','z','time')
BOUNDS={'ejjc':{'ejit','eiyz','eiy2','eiyy'},'ejjd':{'ejip','ejir','ejit','ejjc'},'ejjf':{'ejjd','ejit'},'ejjg':{'ejjf'},'ejjh':{'ejiw','ejeh','ejjd'},'eiyy':{'eiyx'}}

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    abstract(doc,NUM|{'sje','sjd','sky','zzbb','zzbd'}|BOUNDS.get(name,set()));doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='joce'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jocepoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jocepoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jocepoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=600000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(speed=Q(3),time=Q(5)):
    cuts,m=numbers();c=cuts.make;r=cuts.read;speed=Q(speed);time=Q(time)
    beta={Q(0):Q(1),Q(3):Q(5,4),Q(-3):Q(5,4),Q(4):Q(5,3),Q(-4):Q(5,3)}[speed]
    coords={'x':[speed*time,Q(0),Q(0),time],'y':[Q(0),Q(0),Q(0),time/beta],
            'z':[speed*(time+5),Q(0),Q(0),time+5],'time':[Q(0),Q(0),Q(0),(time+5)/beta]}
    def coordinate(rec,axis):
        if rec not in coords or axis not in RECORDS:forbidden()
        return c(Q(coords[rec][RECORDS.index(axis)]))
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(speed),'sky':lambda x:square_root(cuts,x),'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'sjd':lambda a:c(1/r(a)) if r(a) else forbidden(),'zzbb':c,'zzbd':lambda a,b:c(r(a)+r(b)),'zzbg':lambda a,b:r(a)<r(b),'zc5':lambda rec:rec in coords,'zc6':coordinate}
    return cuts,m,coords,norm_factory(cuts,(0,1,2))

@lru_cache(None)
def numeric_checks():
    count=0
    for speed,time in product((-4,-3,0,3,4),(-5,Q(-1,3),0,Q(2,3),7)):
        cuts,m,coords,norm=model(speed,time);c=cuts.make;r=cuts.read;beta=Q(5,3) if abs(speed)==4 else Q(5,4) if abs(speed)==3 else Q(1)
        for n,args in (('ssn',['x','y']),('svf',['x','y']),('svg',['x']),('ejje',['x','y'])):
            assert run(n,args,m), (n,speed,time);count+=1
        # Actual values of the two reciprocal-root constructions agree.
        seen=[];base=m['sca']
        def eq(a,b):seen.append((r(a),r(b)));return base(a,b)
        assert run('ejje',['x','y'],m|{'sca':eq});assert (beta,beta) in seen;count+=1
        # Break only tau; x=vt still holds.
        coords['y'][3]+=1
        assert not run('svf',['x','y'],m) and run('svg',['x'],m) and not run('ejje',['x','y'],m);count+=3
        coords['y'][3]-=1
        # Off-origin current event can satisfy the time formula, but not x=vt.
        coords['x'][0]+=1;coords['y'][3]=beta*(Q(time)-Q(speed)*coords['x'][0]/25)
        assert run('svf',['x','y'],m) and not run('svg',['x'],m) and not run('ejje',['x','y'],m);count+=3
        coords['x'][0]-=1;coords['y'][3]=Q(time)/beta
        if speed and time:
            coords['y'][3]=Q(time)*beta;assert not run('ejje',['x','y'],m);count+=1
        unknowns(lambda mm:run('ejje',['x','y'],mm),m,('zc5','zc6','tc','zb7','sky','sje','sjd'))
    # Native four equations imply the two equations at the spatial origin;
    # generic off-origin events are deliberately not included in the claim.
    for speed,t,dx,y,z in product((-3,3),(-2,2),(0,2),(0,1),(0,1)):
        cuts,m,coords,norm=model(speed,t);x=Q(speed*t+dx);beta=Q(5,4)
        coords['x']=[x,Q(y),Q(z),Q(t)];coords['y']=[beta*(x-speed*t),Q(y),Q(z),beta*(t-speed*x/25)]
        assert run('ssn',['x','y'],m);count+=1
        expected=dx==0
        assert run('ejje',['x','y'],m)==expected;count+=1
        if all(p==0 for p in coords['y'][:3]):assert expected
    cuts,m,coords,norm=model();c=cuts.make
    assert not run('srd',[c(Q(5)),c(Q(3)),c(Q(-5,4))],m);count+=1
    assert not run('srd',[c(Q(5)),c(Q(3)),c(Q(3,5))],m);count+=1
    for speed in (5,6):
        try:run('ejje',['x','y'],m|{'zb7':lambda:c(Q(speed))})
        except ValueError:pass # Singular inverse or square root outside its domain.
        else:raise AssertionError('Out-of-domain transformation silently accepted')
        count+=1
    return dict(cases=count,both_equations_native_and_independently_distinguished=True,positive_reciprocal_root_and_signed_coordinate_time=True,current_four_equations_restrict_to_same_origin=True)

@lru_cache(None)
def bridge_checks():
    cuts,m,coords,norm=model();count=0
    rows={'ejit':{('clock','y','x','context')},'eiyz':{('x',)},'eiy2':{('y',)},'eiyy':{('x','y')}}
    mm=m|{n:relation(rs) for n,rs in rows.items()};args=['clock','y','x','context']
    count+=perturb(lambda mm:run('ejjc',args,mm),mm,rows,norm)
    for axis in range(3):
        coords['y'][axis]=Q(1);assert not run('ejjc',args,mm);coords['y'][axis]=Q(0);count+=1
    assert not run('ejjc',args,mm|{'zb6':lambda:'other'});count+=1
    unknowns(lambda mm:run('ejjc',args,mm),mm,('zc6',))
    # Native same-event existential: K and k records must share one event.
    domain=('a','b')
    for event,lab,own in product(domain,repeat=3):
        rows={'zc4':{(event,)},'eiyx':{(event,lab,'a','context'),(event,own,'b','context')}}
        mm={n:relation(rs) for n,rs in rows.items()}|{'ra':lambda:'a','zbm':lambda:'b'}
        count+=perturb(lambda mm:run('eiyy',[lab,own],mm,domain),mm,rows)
        other='b' if event=='a' else 'a'
        assert not run('eiyy',[lab,own],mm|{'zc4':lambda x:True,'eiyx':relation({(event,lab,'a','context'),(other,own,'b','context')})},domain);count+=1
    return dict(cases=count,same_clock_current_context_ranges_and_correspondence_bound=True,three_origin_components_and_shared_event_required=True)

@lru_cache(None)
def scope_checks():
    count=0;domain=('a','b');pairs=set(product(domain,repeat=2))
    for own,lab in pairs:
        rows={'ejip':{('a','context')},'ejir':{('a','context')},'ejit':{('a',own,lab,'context')},'ejjc':{('a',own,lab,'context')}}
        mm={n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejjd',['a','context'],mm,domain)
        assert check(mm);count+=1
        for n in ('ejip','ejir','ejjc'):
            rs=rows[n]
            for row in rs:
                assert not check(mm|{n:lambda *xs:False});count+=1
                for i in range(len(row)):
                    bad=tuple('other' if i==j else x for j,x in enumerate(row));assert not check(mm|{n:relation({bad})});count+=1
        for other in pairs-{(own,lab)}:
            assert not check(mm|{'ejit':relation(rows['ejit']|{('a',*other,'context')})});count+=1
    cuts,m,coords,norm=model();rows={'ejjd':{('x','context')},'ejit':{('x','y','x','context'),('x','time','z','context')}}
    mm=m|{n:relation(rs) for n,rs in rows.items()};check=lambda mm:run('ejjf',['x','context'],mm,RECORDS)
    assert check(mm);count+=1
    # Either selected event can be wrong; one remaining correct event is insufficient.
    for record,slot in (('y',3),('time',3),('x',0),('z',0)):
        coords[record][slot]+=1;assert not check(mm);coords[record][slot]-=1;count+=1
    assert not check(mm|{'ejjd':lambda *xs:False});count+=1
    # An unselected coordinate pair need not satisfy either equation.
    assert check(mm|{'ejit':relation({('x','y','x','context')})});count+=1
    assert not check(mm|{'ejit':relation(rows['ejit']|{('x','y','z','context')})});count+=1
    unknowns(check,mm,('ejjd','ejit','zc6'))
    return dict(cases=count,all_current_pairs_not_filtered_by_equation_success=True,nonempty_full_time_physical_scope_retained_as_prior_dependency=True,native_equations_applied_to_each_selected_pair=True)

@lru_cache(None)
def presentation_checks():
    count=0
    rows={'ejjf':{('clock','context')}};m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('ejjg',[],mm),m,rows)
    for a,b,c in product((False,True),repeat=3):
        m={'ejiw':lambda:Content(POINTS,(not a,a,not a)),'ejeh':lambda:Content(POINTS,(not b,b,not b)),'ejjd':lambda cl,ctx:c and (cl,ctx)==('clock','context')}
        assert run('ejjh',[],m)==(a and b and c);count+=1
    for name,rows in (
        ('ejji',{'zc':{('equations','author','ejjh','ejjg','section','discourse')},'zdg':{('equations','author','ejjg','section','discourse')}}),
        ('ejjk',{'eir3':{('equations','author','paper','ejjj','discourse')},'ue':{('question','equations','discourse')}})):
        m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run(name,[],mm),m,rows)
        assert run(name,[],m|{'ejjg':forbidden,'ejjh':forbidden,'ejjj':forbidden});count+=1
    return dict(cases=count,same_clock_setup_and_final_transform_as_context=True,author_obviousness_conjunction_and_source_order=True,quoted_claim_not_automatic_proof=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));table={m['id']:m for m in inv['math']};segments=[]
    expected={211:'x',212:'t',213:'τ',214:'τ=11−(vV)2(t−vV2x)',215:'x=vt'}
    for u in inv['units'][118:122]:
        math=[]
        for mid in u['math_ids']:
            e=table[mid];root=ET.fromstring(e['mathml']);flat=re.sub(r'\s','',''.join(root.itertext()));assert flat==expected[int(mid[1:])],(mid,flat)
            if mid=='M0214':assert len(root.findall('.//{http://www.w3.org/1998/Math/MathML}msqrt'))==1 and len(root.findall('.//{http://www.w3.org/1998/Math/MathML}mfrac'))==3
            math.append(dict(id=mid,sha256=e['sha256'],mathml_flat=flat))
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=math))
    assert [s['unit'] for s in segments]==[f'einstein-1905:u{n:04d}' for n in range(119,123)]
    retrieval='artifacts/einstein-origin-clock-setting-v1/retrieval.json';rr=json.loads(read(retrieval));validate_hashes(ROOT,{x['path']:x['sha256'] for x in rr['sources']});paths={INVENTORY,DOC,retrieval,*(x['path'] for x in rr['sources'])}
    return dict(version='einstein-origin-clock-equations-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['904'],segments=segments,observations=['原刊904頁で時計の設定と問いに続くZwischen die Größenからx=vt.までを通読した。x,t,τはいずれも同じ時計の場所を参照し、時間変換式と軌道式の間にundがある。','M0214の係数は1を平方根で割った値で、平方根の中は1−(v/V)²。括弧の中はt−(v/V²)x。M0215はx=vtであり、次のEs ist alsoと比例式は別の導出へ続く。','offenbarを著者が二式の成立を明白として提示する働きとして保持する。固定原文のZwischen die Größenを文法上の書換えで変更しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==340
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations'];assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[337,338])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core();ds={d['name']:d for d in doc['declarations']}
    assert ds['ejjj']['body']['force']=='assert';assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    names={d['name'] for d in extract_document(doc,roots=['ejjg'],statement_indices=[]).document['declarations']}
    assert {'ejip','ejir','ejit','eiyx','eiyy','svf','svg','stw','ejje'}<=names and not {'zac','shd','svj','svk','ejiu'}&names
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=339,prior_whole_unit_judgments_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('bridge',bridge_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    helpers=('check_coordinate_correspondence','check_moving_trip_geometry','check_clock_site_time','check_transverse_time','check_material_relative_frame','check_rod_methods','compose_origin_clock_question','compose_solid_sphere_geometry','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_origin_clock_equations.py','scripts/check_origin_clock_equations.py','tests/test_origin_clock_equations.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='same_origin_clock_current_records_and_two_equations_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0119–u0122の全体通読判断と登録'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
