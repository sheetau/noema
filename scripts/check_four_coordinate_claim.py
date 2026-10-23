"""Check current exact equation scope, reparameterization and author presentation."""
from functools import lru_cache
from fractions import Fraction as Q
from math import isqrt
import json,re
from xml.etree import ElementTree as ET
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,SequenceValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.compose_four_coordinate_claim import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,GROUPS,build

DOC='docs/four-coordinate-claim-v1.md';SOURCE='data/einstein-four-coordinate-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json';PRIOR='data/einstein-transverse-ray-u0073-review-v1.json'
DEPENDENCIES=('reports/spatial-affine-calibration-v1.json','reports/four-coordinates-v1.json','reports/event-coordinate-task-v1.json','reports/affine-time-claim-v1.json','reports/transverse-ray-claim-v1.json')
RS=dict(kind='function',parameters=['number'],result='truth')
CONSTANTS={'yn':'x','yo':'y','yp':'z','zc7':'time','rd':'author','eirf':'paper','eisms':'section','ri':'discourse','zfi':'annotation','zfj':'rewrite','zfk':'beta','zff':'previous'}
DOMAIN=tuple(dict.fromkeys((*CONSTANTS.values(),'first','second','other')))
RECORDS=('x','y','z','time')

@lru_cache(None)
def core_document():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core_document(),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'sje','sjd','sky','eiyz','eiy2','eiyy'}
    if name in ('ei7b','ei7c'):boundaries.add('eiy4')
    if name=='ei7e':boundaries|={'ei7b','spq'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jfcc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jfccpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jfccpoint',arguments=[]))
    elif d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jfccapture',parameters=[d['result']],result='truth'));expr=dict(kind='call',symbol='jfccapture',arguments=[expr])
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('jfccpoint',lambda:'discourse')
    return evaluate_document(doc,individuals=domain,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def model(speed=Q(3),scale=Q(2),point=(7,11,13,2)):
    cuts,m=numbers();c=cuts.make;r=cuts.read;speed=Q(speed);scale=Q(scale);seen=[]
    def sqrt(x):
        n=r(x)
        if n<0:forbidden()
        a=isqrt(n.numerator);b=isqrt(n.denominator)
        if a*a!=n.numerator or b*b!=n.denominator:forbidden()
        return c(Q(a,b))
    def coefficient(v):seen.append(r(v));return c(scale)
    m|={'tc':lambda:c(Q(5)),'zb7':lambda:c(speed),'zeq':lambda:FunctionValue((RS,),RS,coefficient),'sje':lambda a,b:c(r(a)/r(b)) if r(b) else forbidden(),'sjd':lambda a:c(1/r(a)) if r(a) else forbidden(),'sky':sqrt}
    w=r(sqrt(c(25-speed*speed)));beta=5/w;phi=scale*beta
    def result(p):
        x,y,z,t=map(Q,p);return [phi*beta*(x-speed*t),phi*y,phi*z,phi*beta*(t-speed*x/25)]
    first=list(map(Q,point));second=result(first)
    coords={'x':first,'y':second,'z':second.copy(),'time':[v+1 for v in second]}
    m['zc5']=lambda record:record in coords
    m['zc6']=lambda record,role:c(coords[record][RECORDS.index(role)]) if record in coords and role in RECORDS else forbidden()
    scopes={'left':{'x'},'right':{'y','z','time'},'pairs':{('x','y'),('x','z')}}
    m|={'eiyz':lambda record:record in scopes['left'],'eiy2':lambda record:record in scopes['right'],'eiyy':lambda a,b:(a,b) in scopes['pairs']}
    return cuts,m,coords,scopes,result,seen

def capture(name,m):
    out=[]
    assert run(name,[],m|{'jfccapture':lambda value:out.append(value) is None})
    assert len(out)==1;return out[0]

def numeric_sequence(cuts,coords,result,element):
    # This explicit rational boundary lets the native general equation checker
    # run without pretending arbitrary predicate cuts can be decoded to numbers.
    positions=(3,0,1,2)
    terms=tuple(FunctionValue(tuple(element['parameters']),element['result'],lambda a,b,left,i=i:cuts.make(coords[b][i] if left else result(coords[a])[i])) for i in positions)
    return SequenceValue(terms,json.dumps(element,sort_keys=True,separators=(',',':')))

def matches(seq,coords,result):
    if len(seq.items)!=4:return False
    for a,b in (('x','y'),('x','time'),('z','y')):
        values=[coords[b],result(coords[a])]
        probes={Q(0)}|{x+d for side in values for x in side for d in (Q(-1,64),Q(0),Q(1,64))}
        for eq,i in zip(seq.items,(3,0,1,2)):
            for left,side in ((True,0),(False,1)):
                cut=eq(a,b,left)
                if any(cut(p)!=(p<values[side][i]) for p in probes):return False
    return True

@lru_cache(None)
def numeric_checks():
    count=0
    for speed,scale,point in ((3,2,(7,11,13,2)),(4,Q(3,2),(-2,3,7,5)),(0,2,(1,2,3,4)),(3,0,(7,11,13,2)),(3,-2,(7,11,13,2))):
        cuts,m,coords,scopes,result,seen=model(speed,scale,point);c=cuts.make;r=cuts.read
        assert [run(n,['x','y'],m) for n in ('sph','spg')]==[True,True];count+=2
        beta=Q(5)/r(m['sky'](c(25-Q(speed)**2)))
        assert run('spa',[c(Q(5)),c(Q(speed)),c(beta)],m);count+=1
        for wrong in (-beta,Q(speed,5),beta+1):
            assert run('spa',[c(Q(5)),c(Q(speed)),c(wrong)],m)==(wrong==beta);count+=1
        for slot in range(4):
            coords['y'][slot]+=1;assert [run(n,['x','y'],m) for n in ('sph','spg')]==[False,False];coords['y'][slot]-=1;count+=2
        if speed!=0 and scale!=0:
            # Keeping the old coefficient as the new phi changes all four RHSs.
            oldphi=m|{'spc':lambda:FunctionValue((RS,),RS,lambda v:c(Q(scale)))}
            doc,slots=fixture('spg');changed=parse(format_graph(doc,'compact'))
            abstract(changed,{'spc'})
            mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|oldphi|{slots[0]:lambda:'x',slots[1]:lambda:'y'}
            got=evaluate_document(changed,individuals=DOMAIN,situations=('context','discourse','other'),primitives={d['name']:mm.get(d['name'],forbidden) for d in changed['declarations'] if d['kind']=='primitive'},max_steps=700000)[0]['value']
            assert not got;count+=1
        assert set(seen)=={Q(speed)},seen
        unknowns(lambda mm:run('spg',['x','y'],mm),m,('tc','zb7','zeq','sky','sjd','sje','zc6','zc5'))
    report=json.loads(read('reports/four-coordinates-v1.json'));validate_hashes(ROOT,report['source_sha256'])
    return dict(cases=count,both_four_equation_forms_agree_on_non_light_inputs=True,phi_is_a_times_beta_not_the_old_coefficient=True,beta_is_positive_reciprocal_root_not_v_over_V=True,all_four_outputs_and_same_speed_checked=True,existing_polynomial_reparameterization_evidence_preserved=True)

@lru_cache(None)
def system_checks():
    count=0
    for point in ((7,11,13,2),(-2,3,7,5),(0,0,0,0)):
        cuts,m,coords,scopes,result,seen=model(point=point)
        for n in ('ei67','ei7a'):
            seq=capture(n,m);assert matches(seq,coords,result);count+=1
            # Independently check every component and both sides of the native
            # constructed sequence, including a wrong output pair.
            for record in ('x','y'):
                for slot in range(4):
                    coords[record][slot]+=1;assert matches(capture(n,m),coords,result);coords[record][slot]-=1;count+=1
            seq=capture(n,m);reversed_seq=SequenceValue(tuple(reversed(seq.items)),seq.element_type)
            if point!=(0,0,0,0):assert not matches(reversed_seq,coords,result);count+=1
    cuts,m,coords,scopes,result,seen=model();seq=capture('ei7a',m)
    element=next(d['result']['element'] for d in core_document()['declarations'] if d['name']=='ei7a')
    actual=numeric_sequence(cuts,coords,result,element)
    assert run('eiy4',[actual],m,domain=RECORDS);count+=1
    for items in ((),actual.items[:3],actual.items[1:]):
        bad=SequenceValue(items,actual.element_type)
        # Missing equations can accidentally agree on a small range; give a
        # distinguishing bad output in precisely the dropped component.
        old=coords['time'][:];coords['time'][:]=coords['y'][:]
        if len(items)==3:coords['time'][2 if items==actual.items[:3] else 3]+=1
        assert not run('eiy4',[bad],m,domain=RECORDS);count+=1;coords['time'][:]=old
    unknowns(lambda mm:run('eiy4',[actual],mm,domain=RECORDS),m,('eiyz','eiy2','eiyy','ba','sca'))
    return dict(cases=count,all_four_native_equation_sides_and_order_checked=True,current_equation_task_checked_with_explicit_rational_cut_boundary=True,empty_and_missing_equations_rejected_on_distinguishing_outputs=True,finite_cut_probes_not_general_cut_equality=True)

@lru_cache(None)
def graph_checks():
    cuts,m,coords,scopes,result,seen=model();count=0
    m['eiy4']=lambda seq:matches(seq,coords,result)
    for label in ('baseline','omit_alias','spurious_relation','omit_source_pair','empty_left','extra_unmatched_left','different_value_alias'):
        scopes['left']={'x'};scopes['right']={'y','z','time'};scopes['pairs']={('x','y'),('x','z')};old=coords['z'][:]
        if label=='omit_alias':scopes['pairs'].remove(('x','z'))
        if label=='spurious_relation':scopes['pairs'].add(('x','time'))
        if label=='omit_source_pair':scopes['pairs']=set()
        if label=='empty_left':scopes['left']=set()
        if label=='extra_unmatched_left':scopes['left'].add('z')
        if label=='different_value_alias':coords['z']=[v+2 for v in old];scopes['pairs'].remove(('x','z'))
        expected=label in ('baseline','different_value_alias')
        for name in ('ei7b','ei7c'):
            assert run(name,[],m,domain=RECORDS)==expected,(label,name);count+=1
        coords['z'][:]=old
    scopes['left']={'x'};scopes['right']={'y','z','time'};scopes['pairs']={('x','y'),('x','z')}
    for name in ('ei7b','ei7c'):
        assert not run(name,[],m|{'eiy4':lambda seq:False},domain=RECORDS);count+=1
        unknowns(lambda mm:run(name,[],mm,domain=RECORDS),m,('eiyz','eiy2','eiyy','eiy4','zc6','zc5','sky','zeq'))
    return dict(cases=count,native_nonempty_functional_scope_and_bidirectional_solution_set_checked=True,equal_value_alias_and_extra_missing_pairs_distinguished=True,current_equation_question_not_replaced_by_old_coordinate_scopes=True)

@lru_cache(None)
def presentation_checks():
    rows=[('ei7d',{'zfl':{('annotation','author','ei66','ei7b','section','discourse')}}),('ei7f',{'zd3':{('rewrite','author','ei7e','ei7b','ei7c','section','discourse')}}),('ei7i',{'uh':{('beta','author','spq','section','discourse')}})]
    for body,message,author,node,previous in GROUPS:
        relations={'eir3':{(CONSTANTS[node],'author','paper',message,'discourse')},'ue':{(CONSTANTS[previous],CONSTANTS[node],'discourse')}}
        if author=='ei7h':relations['zfl']={('annotation','author','ei66','ei7b','section','discourse')}
        rows.append((author,relations))
    count=0
    for name,relations in rows:
        m={n:relation(rs) for n,rs in relations.items()};count+=perturb(lambda mm:run(name,[],mm),m,relations)
        assert run(name,[],m|{n:forbidden for n in ('ei66','ei7b','ei7c','ei7e','spq')});count+=1
    return dict(cases=count,interpretive_annotation_outside_author_message=True,rewrite_premise_before_after_and_beta_specification_distinct=True,same_author_paper_section_and_source_order_required=True,quoted_contents_not_executed=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    readings={'M0134':'x′','M0135':'τ=φ(v)β(t−vx/V²); ξ=φ(v)β(x−vt); η=φ(v)y; ζ=φ(v)z','M0136':'β=1/√(1−(v/V)²)'}
    for n,flat in zip(readings,('x′','τ=φ(v)β(t−vV2x),ξ=φ(v)β(x−vt),η=φ(v)y,ζ=φ(v)z,','β=11−(vV)2')):assert ''.join(ET.fromstring(math[n]['mathml']).itertext())==flat
    for i,u in enumerate(inv['units'][80:84]):
        assert u['id']==f'einstein-1905:u{81+i:04d}'
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],text=u['text'],source_nonblank_characters=len(re.sub(r'\s|\[M\d+\]','',u['text'])),math=[dict(id=n,sha256=math[n]['sha256'],reading=readings[n],mathml_flat=''.join(ET.fromstring(math[n]['mathml']).itertext())) for n in u['math_ids']]))
    retrieval='artifacts/einstein-longitudinal-elimination-v1/retrieval.json';retrieved=json.loads(read(retrieval));validate_hashes(ROOT,{r['path']:r['sha256'] for r in retrieved['sources']})
    paths={INVENTORY,DOC,retrieval,*(r['path'] for r in retrieved['sources'])}
    return dict(version='einstein-four-coordinate-source-reading-v1',reviewer='assistant_visual_and_text_review',pages=['900'],segments=segments,observations=['原刊900頁のSetzen wir für x′から四式、wobei、βの分数表示までを前後と合わせて通読した。','四式の順はτ,ξ,η,ζ。τとξにはφ(v)β、ηとζにはφ(v)だけが掛かる。τの括弧はt−(v/V²)x、ξの括弧はx−vtである。','βは1/√(1−(v/V)²)。平方根、商全体の二乗、正の枝を現在の速度範囲へ結ぶ。','以前のa=φ(v)と同じ文字を使うが、四式はφ_new=a*βの再表示として読む。先行係数の値をそのまま新φへ移すと四式は同じにならない。','光線上の三式を全測定域へ伸ばす際の同じアフィン行・原点・三光線の十分条件を解釈注記として明示し、原文が逐一述べた条件にしない。','四式内のコンマはMathMLに固定される。次の未知関数と加法定数の文はu0085に残す。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-2]==old.document['statements'] and len(new.document['statements'])==302
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[295,296,297,298,299])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=core_document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[m]['body']['force']=='assert' for _,m,_,_,_ in GROUPS)
    assert 'zfl' not in extract_document(doc,roots=['ei7g'],statement_indices=[]).retained_symbols
    assert 'zfl' in extract_document(doc,roots=['ei7h'],statement_indices=[]).retained_symbols
    for n in ('ei7b','ei7c','ei7d'):
        selected=extract_document(doc,roots=[n],statement_indices=[])
        assert not set(selected.retained_symbols)&{'spo','spi','spj','spk','spr','shi','sio','shf','shg','she','shd'},n
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=INDEX,prior_whole_unit_judgment_preserved=True,additional_interpretation_not_attributed_as_author_utterance=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('systems',system_checks),('scope',graph_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_four_coordinate_claim.py','scripts/check_four_coordinate_claim.py','tests/test_four_coordinate_claim.py','scripts/check_coordinate_correspondence.py','scripts/check_moving_trip_geometry.py','scripts/check_material_relative_frame.py','scripts/check_clock_site_time.py','scripts/check_rod_methods.py','scripts/compose_coordinate_correspondence.py','scripts/compose_limits.py','scripts/compose_material_relative_frame.py','scripts/compose_relativity_conjecture.py','scripts/compose_two_postulates.py'}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=[INDEX] if i<2 else [INDEX,INDEX+1],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for i,s in enumerate(source_record()['segments'])])
    return dict(status='current_four_coordinate_equations_reparameterization_and_beta_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},general_real_physical_derivation_proved=False,semantic_equivalence_automatically_proved=False,remaining=['u0081–u0084の全文通読判断登録','u0085以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
