"""Check shared current records, calibration, origins and composed four maps."""
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
from scripts.check_moving_trip_geometry import NUM,norm_factory
from scripts.check_clock_site_time import relation,perturb,unknowns,forbidden
from scripts.check_velocity_composition_claim import arithmetic
from scripts.check_parallel_composition import transform
from scripts.compose_parallel_current_records import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build

DOC='docs/parallel-current-records-v1.md';SOURCE='data/einstein-parallel-current-source-reading-v1.json'
INVENTORY='artifacts/written-units-v1/einstein-1905.json'
PRIORS=tuple(f'data/einstein-velocity-light-u{n:04d}-review-v1.json' for n in (145,146))
DEPENDENCIES=('reports/third-frame-geometry-v1.json','reports/parallel-composition-v1.json','reports/velocity-light-claim-v1.json')
CONSTANTS={'ra':'K','zbm':'k','zlo':'third','yn':'x','yo':'y','yp':'z','zc7':'time','ta':'length','rb':'duration','zb6':'context','zlr':'intro','zls':'result','rd':'author','zlq':'scope','ri':'discourse'}
DOMAIN=('K','k','third','event','other','first','middle','last','alias','origin','x','y','z','time','length','duration','intro','result','author','scope')
POINTS=('context','discourse','other')

@lru_cache(None)
def core():return parse(read(CORE))

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(core(),roots=[name],statement_indices=[]).document
    bounds=NUM|{'sjd','sjt','sky','eiyx','shh','eja2','eivz'}
    if name=='ejqy':bounds|={'ejqx'}
    if name in ('ejq2','ejq3'):bounds|={'ejqw','ejqz'}
    if name=='ejqz':bounds|={'ejqv'}
    if name=='ejq4':bounds|={'ejqy'}
    if name in ('ejq5','ejq6'):bounds|={'ejq2','ejq3'}
    if name=='ejq7':bounds|={'ejq4','ejq5'}
    if name=='eja2':bounds.remove('eja2');bounds|={'eioj','sfc'}
    abstract(doc,bounds);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[]
    for i,p in enumerate(d['parameters']):
        n='jpcr'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    expr=dict(kind='call',symbol=name,arguments=[dict(kind='call',symbol=n,arguments=[]) for n in slots])
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jpcrpoint',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='jpcrpoint',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,domain=DOMAIN):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in CONSTANTS.items()}|{'jpcrpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0
    for speed,moving in ((3,3),(3,-3),(0,3),(3,0),(0,0),(-3,-4),(3,4)):
        a=list(map(Q,(7,3,4,2)));b=transform(a,Q(speed));d=transform(b,Q(moving));coords={'first':a,'middle':b,'last':d}
        mm=m|{'zc5':lambda rec:rec in coords,'zc6':lambda rec,role:c(coords[rec][('x','y','z','time').index(role)])}
        combined=Q(speed+moving)/(1+Q(speed*moving,25))
        chain=lambda pp:run('s4m',['first','middle','last',c(5),c(speed),c(moving)],pp)
        direct=lambda pp:run('s4l',['first','last',c(5),c(combined)],pp)
        assert chain(mm) and direct(mm);count+=2
        for rec,i in product(('middle','last'),range(4)):
            coords[rec][i]+=1
            assert not chain(mm);assert direct(mm)==(rec=='middle');count+=2
            coords[rec][i]-=1
        # Exercise the new higher-order bindings with native equations.
        base=mm|{'ejqw':lambda *xs:xs==('K','k','third','context'),'ejqz':lambda f,g,h,ctx,rel:(f,g,h,ctx)==('K','k','third','context') and rel('first','middle','last')}
        args=['K','k','third',c(5),c(speed),c(moving),'context']
        assert run('ejq2',args,base) and run('ejq3',args,base);count+=2
        for name in ('ejq2','ejq3'):
            for patch in ({'ejqw':lambda *xs:False},{'ejqz':lambda *xs:False}):assert not run(name,args,base|patch);count+=1
        if speed==moving==3:
            assert combined==Q(75,17)
            for i in (0,3):coords['last'][i]*=Q(25,34)
            assert not chain(mm) and not direct(mm);count+=2
        unknowns(chain,mm,('zc5','zc6','sky','sjd'))
    return dict(cases=count,native_four_components_and_shared_middle_checked=True,new_relation_lambdas_use_exact_speeds=True,zero_and_negative_speeds_retained=True,beta_uses_composed_speed=True)

@lru_cache(None)
def record_checks():
    count=0;frames=['K','k','third'];records=['first','middle','last'];domain=('K','k','third','event','other','first','middle','last','alias')
    rows={'zc4':{('event',)},'eiyx':{('event',rec,frame,'context') for rec,frame in zip(records,frames)}}
    base={n:relation(rs) for n,rs in rows.items()}
    args=frames+['event']+records+['context'];check=lambda mm:run('ejqv',args,mm,domain)
    count+=perturb(check,base,rows)
    for i,j in ((0,1),(0,2),(1,2)):
        bad=args.copy();bad[j]=bad[i];assert not run('ejqv',bad,{'zc4':lambda e:True,'eiyx':lambda *xs:True},domain);count+=1
    charts={(event,rec,frame,'context') for event in ('event','other') for rec,frame in zip(records,frames)}|{('event','alias','third','context')}
    m={'zc4':lambda e:e in ('event','other'),'eiyx':lambda *xs:xs in charts,'shh':lambda a,b:a==b or {a,b}<={'last','alias'}}
    check=lambda mm:run('ejqw',frames+['context'],mm,domain)
    assert check(m);count+=1
    for event,frame in product(('event','other'),frames):
        assert not check(m|{'eiyx':lambda e,t,f,c,e0=event,f0=frame:(e,t,f,c) in charts and (e,f)!=(e0,f0)});count+=1
    for patch in ({'zc4':lambda e:False},{'shh':lambda a,b:a==b}):assert not check(m|patch);count+=1
    unknowns(check,m,('zc4','eiyx','shh'))
    return dict(cases=count,current_same_event_records_and_distinct_frames=True,nonempty_complete_scope_and_value_uniqueness=True,identical_value_aliases_allowed=True)

@lru_cache(None)
def geometry_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;norm=norm_factory(cuts,());count=0
    frames=['K','k','third'];records=['first','middle','last'];coords={rec:[Q(0)]*4 for rec in records}
    rows={'zc4':{('event',)},'eiyx':{('event',rec,f,'context') for rec,f in zip(records,frames)},'zbv':{(f,'origin','context') for f in frames},'cb':{('event','origin',f) for f in frames}}
    m|={n:relation(rs) for n,rs in rows.items()};m|={'zbn':lambda f,ctx,frames=tuple(frames):'origin' if f in frames and ctx=='context' else forbidden(),'zc6':lambda rec,role:c(coords[rec][('x','y','z','time').index(role)])}
    args=frames+['event']+records+['context'];check=lambda mm:run('ejqx',args,mm)
    count+=perturb(check,m,rows)
    for rec,i in product(records,range(4)):
        coords[rec][i]=Q(1);assert not check(m);coords[rec][i]=Q(0);count+=1
    unknowns(check,m,('zbn','zc6'))
    # Four existential slots use two values; the actual origin body was checked above.
    small=('a','b');frames=['a','b','a']
    # Keep cuts and numeric oracles from one fixture.
    base=m|{'eisdd':lambda *xs:True,'eja2':lambda *xs:True,'ta':lambda:'a','rb':lambda:'b'}
    for row in product(small,repeat=4):
        chosen=tuple(frames)+row+('context',)
        mm=base|{'ejqx':lambda *xs,chosen=chosen:xs==chosen}
        args=frames+[c(5),c(3),c(-3),'context']
        assert run('ejqy',args,mm,small);count+=1
        assert not run('ejqy',args,mm|{'ejqx':lambda *xs:False},small);count+=1
    # Typed physical arguments and both signed bounds are checked independently.
    rows={'eisdd':{(f,'a','b','context') for f in frames},'eja2':{('a','b',Q(3),'context'),('b','a',Q(-3),'context')}}
    mm=base|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{'ejqx':lambda *xs:xs==tuple(frames)+('a','b','a','b','context')}
    count+=perturb(lambda pp:run('ejqy',args,pp,small),mm,rows,norm)
    for light,speed,moving,expected in ((5,0,0,True),(5,-3,3,True),(5,5,0,False),(5,0,-5,False),(0,0,0,False),(-5,0,0,False)):
        assert run('ejqy',frames+list(map(c,(light,speed,moving)))+['context'],mm|{'eja2':lambda *xs:True},small)==expected;count+=1
    # Native eja2: all selected origin positions must be on the intermediate axis.
    rows={'eioj':{('k','third','length','duration','context')},'sfc':{('k','third','context')},'eisk7':{('third','origin','context')}}
    velocities={'x':Q(-3),'y':Q(0),'z':Q(0)};positions={(t,a):Q(0) for t in DOMAIN for a in ('y','z')}
    mm=m|{n:relation(rs) for n,rs in rows.items()}|{'eisla':lambda f,g,t,ctx:(f,g,ctx)==('k','third','context') and t in ('event','other'),'eislc':lambda f,g,lu,tu,a,ctx:c(velocities[a]) if (f,g,lu,tu,ctx)==('k','third','length','duration','context') else forbidden(),'ym':lambda o,t,f,lu,a,ctx:c(positions[t,a]) if (o,f,lu,ctx)==('origin','k','length','context') else forbidden()}
    check=lambda pp:run('eja2',['k','third',c(-3),'context'],pp)
    count+=perturb(check,mm,rows)
    for t,a in product(('event','other'),('y','z')):
        positions[t,a]=Q(1);assert not check(mm);positions[t,a]=Q(0);count+=1
    for a in velocities:
        velocities[a]+=1;assert not check(mm);velocities[a]-=1;count+=1
    unknowns(check,mm,('zbn','eislc','ym','eisla'))
    return dict(cases=count,all_twelve_origin_coordinates_checked=True,three_calibrations_and_both_full_frame_motions_bound=True,existential_four_slot_binding_on_two_value_domain=True,native_origin_axis_constraint_checked=True)

@lru_cache(None)
def scope_checks():
    cuts,m=arithmetic();c=lambda x:cuts.make(Q(x));r=cuts.read;count=0;small=('a','b')
    sort=dict(kind='function',parameters=['individual']*3,result='truth')
    for row in product(small,repeat=4):
        frames=('a','b','a');selected=frames+row+('context',)
        mm={'ejqv':lambda *xs,selected=selected:xs==selected}
        predicate=FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs,row=row:xs==row[1:])
        assert run('ejqz',[*frames,'context',predicate],mm,small);count+=1
        wrong=FunctionValue(tuple(sort['parameters']),sort['result'],lambda *xs:False)
        assert not run('ejqz',[*frames,'context',wrong],mm,small);count+=1
    fixed=('K','k','third',Q(5),Q(3),Q(-3),'context');norm=norm_factory(cuts,())
    base=m|{'tc':lambda:c(5),'zb7':lambda:c(3),'zlt':lambda:c(-3)}
    for name,dep in (('ejq5','ejq2'),('ejq6','ejq3')):
        rows={dep:{fixed}};mm=base|{dep:lambda *xs:norm(xs)==fixed}
        count+=perturb(lambda pp:run(name,[],pp),mm,rows,norm)
    rows={'eivz':{('context',)},'ejqy':{fixed}};mm=base|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda pp:run('ejq4',[],pp),mm,rows,norm)
    for a,b in product((False,True),repeat=2):
        mm={'ejq4':lambda:Content(POINTS,(a,a,a)),'ejq5':lambda:Content(POINTS,(b,b,b))}
        assert run('ejq7',[],mm)==(a and b);count+=1
    # Attribution quotes the new contents without evaluating their physics.
    doc=core();doc=dict(doc,statements=[doc['statements'][i] for i in range(2)])
    rows={'ug':{('intro','author','ejq4','scope','discourse')},'zc':{('result','author','ejq7','ejq6','scope','discourse')}}
    normalize=lambda xs:tuple(json.loads(x.syntax)['symbol'] if hasattr(x,'syntax') else x for x in xs)
    def evaluate(mm):
        constants={n:lambda x=x:x for n,x in CONSTANTS.items()};mm=constants|mm
        return [x['value'] for x in evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})]
    mm={n:lambda *xs,rs=rs:normalize(xs) in rs for n,rs in rows.items()};assert evaluate(mm)==[True,True];count+=2
    for n,i in (('ug',0),('zc',1)):
        result=evaluate(mm|{n:lambda *xs:False});assert result[i] is False and result[1-i] is True;count+=2
    return dict(cases=count,all_four_universal_slots_bound=True,same_current_context_frames_and_speeds=True,setup_and_double_application_both_required=True,quoted_consequence_not_certified_as_true=True)

@lru_cache(None)
def source_record():
    inv=json.loads(read(INVENTORY));math={m['id']:m for m in inv['math']};segments=[]
    expected=('U','v','K','k','k','k′','Ξ','w','x,y,z,t','k′','v','v+w1+vwV2')
    actual=[]
    for u,sha in zip(inv['units'][146:149],('a5afd9f3d9303b85f2c3087f21c22c91bed58468fbe6476cecba17c20f531edb','0b7c6a7e073d4eb42a3e9e19512f65774c2707669a3e922d7bac12e86e5c66c3','b8661ae860024c11335e78af7f6526514218c36be58198b1ce8fc02a98574611')):
        assert digest(u['text'].encode())==u['text_sha256']==sha
        entries=[]
        for n in u['math_ids']:
            e=math[n];assert digest(e['mathml'].encode())==e['sha256'];flat=re.sub(r'\s','',''.join(ET.fromstring(e['mathml']).itertext()));actual.append(flat)
            entries.append(dict(id=n,sha256=e['sha256'],mathml_flat=flat))
        start=u['text'].index('Führen wir') if u['id'].endswith('0147') else 0
        end=u['text'].index(';')+1 if u['id'].endswith('0149') else len(u['text'])
        segments.append(dict(unit=u['id'],unit_sha256=sha,range=[start,end],text=u['text'][start:end],math=entries))
    assert tuple(actual)==expected
    paths={INVENTORY,DOC,'artifacts/written-facsimiles-v1/einstein-1905-p906.jpg','artifacts/written-facsimiles-v1/einstein-1905-unlp-p907-0.jpg','artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf','data/field-common-scale-facsimile-v1.json'}
    pdf='artifacts/written-facsimiles-v1/einstein-1905-unlp.pdf';assert digest((ROOT/pdf).read_bytes())=='d3c8466013f4a5c5773e2addaf7a728cbaf31e01e2387d1a4ff7cb759acbc803'
    return dict(version='einstein-parallel-current-source-reading-v1',status='dependency_reading_not_whole_unit_judgment',pages=['906','907'],segments=segments,facsimile_907=dict(pdf=pdf,file_page=17,method='pypdf single embedded page image extraction; visual inspection of printed page 907'),observations=['906頁の条件文・第三系k′・Ξ軸・速度w・Kのx,y,z,tと対応するk′の量・§3の速度vだけの置換を照合した。','M0285の分子v+w、分母1+vw/V²と907頁冒頭trittを一つの文として読んだ。','その後のman sieht daraus、群、挿入句wie dies sein mußも確認したが、この依存群の完了とは数えない。','§3と同じ式の適用規約として、同じ校正と共通原点・零時刻を明示する。前段の点の速度と第三系の速度を無条件に同一視しない。'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert len(new.document['statements'])==len(old.document['statements'])==356
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==list(INDICES)
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,selection in zip(PRIORS,([143,144],[144])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,selection)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    names=set(selection_binding(new,[145,146])['dependencies'])
    assert {'ejqv','ejqw','ejqx','ejqy','ejqz','ejq2','ejq3','ejq4','ejq5','ejq6','ejq7','eivz','eja2','eiyx','eisdd','s4l','s4m','s3j','sgv','shh'}<=names
    assert not names&{'shd','zgj','s4n','s4o','s4p','s4q','s4r','s4s','zgi','zlp','zkq'}
    assert not [d for d in new.document['declarations'][len(old.document['declarations']):] if d['kind']=='primitive']
    for style in ('compact','full'):
        body=format_graph(core(),style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==core()
    assert source_record()==json.loads(read(SOURCE))
    return dict(new_definitions=len(MEANINGS),new_primitives=0,replaced_partial_statements=list(INDICES),other_statements_preserved=354,prior_judgments_preserved=True,current_physics_transitively_connected=True,legacy_third_frame_record_paths_excluded=True,whole_unit_review_not_claimed=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:f() for n,f in [('numeric',numeric_checks),('records',record_checks),('geometry',geometry_checks),('scope',scope_checks),('structure',structure_checks)]}
    helpers=('compose_velocity_light_claim','compose_material_relative_frame','compose_relativity_conjecture','compose_two_postulates','compose_limits','check_clock_site_time','check_moving_trip_geometry','check_coordinate_correspondence','check_velocity_composition_claim','check_parallel_composition','audit_opening_scope')
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,*PRIORS,*DEPENDENCIES,'scripts/compose_parallel_current_records.py','scripts/check_parallel_current_records.py','tests/test_parallel_current_records.py',*(f'scripts/{n}.py' for n in helpers)}
    alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],statements=list(INDICES),definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source_record()['segments']])
    return dict(status='current_three_frame_composition_dependencies_connected',document=FULL,**results,alignment=alignment,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['過去の別導出と現行の同方向の結論ejprへの接続','第三系の命名・§3参照と本文順序の統合','全許容速度の群の主張と必要性の候補選定','u0147–u0149の全単位意味判断'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
