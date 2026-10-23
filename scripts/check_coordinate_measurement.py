"""Check actual calibrated measurements separately from signed geometry."""
from functools import lru_cache
from fractions import Fraction as Q
from copy import deepcopy
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
from scripts.check_material_relative_frame import RS,FS
from scripts.check_rod_methods import value
from scripts.compose_coordinate_measurement import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/coordinate-measurement-v1.md';SOURCE='data/einstein-coordinate-measurement-source-reading-v1.json'
SOURCE_PARENT='data/einstein-axis-projection-source-reading-v1.json'
PRIOR='data/einstein-parallel-choice-review-v1.json'
DEPENDENCIES=('reports/axis-projection-v1.json','reports/point-position-v1.json','reports/rod-methods-v1.json')
DOMAIN=('a','b');POINTS=('context','initial')

def forbidden(*xs):raise ValueError('Unknown coordinate-measurement input')
def constants():return {n:lambda x=x:x for n,x in {'ta':'a','rb':'b','yn':'a','yo':'b','yp':'a','zb4':'initial'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eipw','eigy','eixb'}
    if name=='eixg':boundaries|={'eixf'}
    if name=='eixh':boundaries|={'eixg'}
    if name=='eixi':boundaries|={'eixh'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name)
    if mode=='instance':
        bound=[]
        def walk(node):
            if isinstance(node,list):return [walk(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind') in ('forall','exists') and node.get('sort')==RS:
                bound.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
            return {k:walk(v) for k,v in node.items()}
        d['body']=walk(d['body']);d['parameters']+=bound;assert len(bound)==1
    slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jcm'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots),(name,len(args),len(slots))
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=400000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown coordinate-measurement' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                wrong=tuple('wrong' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{wrong}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def magnitude_checks():
    cuts,m=numbers();c=cuts.make;count=0
    for length in (-3,-1,0,1,3,Q(1,2)):
        for signed in (-3,-1,0,1,3,Q(-1,2),Q(1,2)):
            assert run('eixc',[c(Q(length)),c(Q(signed))],m)==(length>=0 and length==abs(signed));count+=1
    assert not run('eixc',[c(Q(2)),c(Q(-2))],m|{'ba':lambda x:False});count+=1
    unknowns(lambda mm:run('eixc',[c(Q(2)),c(Q(-2))],mm),m,('ba','bc','bb','shv','sca'))
    return dict(cases=count,zero_negative_signed_and_nonnegative_magnitude_distinguished=True)

def setup(length=Q(3)):
    cuts,m=numbers();c=cuts.make;r=cuts.read
    families={a:FunctionValue(('individual',),FS,lambda p,a=a:FunctionValue((RS,),RS,lambda t:c(Q((1 if p=='a' else 2)*(1 if a=='a' else 4))))) for a in DOMAIN}
    def family(b,f,lu,tu,a,ctx):
        if (b,f,lu,tu,ctx)!=('b','a','a','b','context') or a not in DOMAIN:forbidden()
        return families[a]
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in DOMAIN for t in (0,1,2))
            forbidden()
        return tuple(one(x) for x in xs)
    members=FunctionValue(('individual',),'truth',lambda p:p=='b')
    h=['b','a','context','a','b',c(Q(0)),c(Q(2)),members,families['a'],families['b'],families['a']]
    rows={'xc':{('b',)},'va':{('a',)},'ti':{('a',)},'ci':{('b',)},'eisej':{('b','b','context')},'eipw':{('b','a','context')},'eigy':{norm(h)},'eisef':{('b','b','a','a','b',Q(0),Q(2),'context')},'xb':{('a',)},'eisnc':{('a','b','a','b','a','a',length,'context')},'xh':{('a','b','a','b','a','a',length,'context')},'th':{('a','b','a','a',length)}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eislu':family,'eirh':lambda b,p,ctx:(b,p,ctx)==('b','b','context')}
    args=['a','b','b','a','b','a',c(length),'context']
    return cuts,m,rows,norm,args

@lru_cache(None)
def instrument_checks():
    cuts,m,rows,norm,_=setup();args=['b','b','a','context']
    selected={n:rows[n] for n in ('xc','va','ti','ci','eisej','eipw','eigy','eisef')}
    check=lambda mm:run('eixd',args,mm);count=perturb(check,m,selected,norm)
    assert not check(m|{'eisej':lambda *xs:xs in rows['eisej']|{('a','b','context')}});count+=1
    assert not check(m|{'eirh':lambda *xs:True});count+=1
    original=m['eislu']
    def wrong(*xs):
        fn=original(*xs)
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,lambda t:cuts.make(cuts.read(fn(p)(t))+1)))
    assert not check(m|{'eislu':wrong});count+=1
    unknowns(check,m,('eislu','eirh','eisls','eislt'))
    return dict(cases=count,single_given_ruler_is_entire_tool_range=True,same_calibrated_method_interval_and_complete_rigid_history=True)

@lru_cache(None)
def procedure_checks():
    cuts,m,rows,norm,args=setup();check=lambda mm:run('eixe',args,mm)
    count=perturb(check,m,{n:rows[n] for n in ('xb','eisnc','xh','th')},norm)
    for length in (Q(-3),Q(0),Q(3)):
        _,mm,_,_,aa=setup(length);assert run('eixe',aa,mm)==(length>=0);count+=1
    # Calibration of another method cannot certify this procedure.
    changed={('b','a','a','a','b',Q(0),Q(2),'context')}
    assert not check(m|{'eisef':lambda *xs:norm(xs) in changed});count+=1
    return dict(cases=count,actual_procedure_reading_and_distance_all_required=True,calibration_of_different_method_rejected=True,zero_distance_included=True)

@lru_cache(None)
def projection_checks():
    count=0
    for signed in (Q(-3),Q(0),Q(3)):
        cuts,m,rows,norm,_=setup(abs(signed));c=cuts.make
        physical=['b','a','b','a','b','a','b','context']
        geom=norm(physical+[c(signed)]);m['eixb']=lambda *xs:norm(xs)==geom
        args=physical+['a','b','b',c(signed),c(abs(signed))]
        check=lambda mm:run('eixf',args,mm)
        count+=perturb(check,m,{'eixb':{geom}},norm)
        assert not run('eixf',args[:-1]+[c(abs(signed)+1)],m);count+=1
        unknowns(check,m,('eisnc','xh','th','eisef'))
    return dict(cases=count,same_origin_projection_axis_role_value_and_distance=True,negative_and_zero_coordinates_use_nonnegative_measurements=True)

@lru_cache(None)
def identity_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    physical=['b','a','b','a','b','a','b','context'];args=physical+['a','b',c(Q(-3)),c(Q(3))]
    expected=norm(physical+['a','b','b',c(Q(-3)),c(Q(3))])
    rows={'eixf':{expected},'zbx':{('a','b','context')}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    m|={'zby':lambda f,ctx:'b','zbn':lambda f,ctx:'a','zbo':lambda f,role,ctx:'b','eismu':lambda axis,f,ctx:'b'}
    check=lambda mm:run('eixg',args,mm);count=perturb(check,m,rows,norm)
    for n in ('zby','zbn','zbo'):
        old=m[n]
        def wrong(*xs,old=old):return ('b' if old(*xs)=='a' else 'a') if xs[-1]=='initial' else old(*xs)
        assert not check(m|{n:wrong});count+=1
    assert not check(m|{'eismu':lambda *xs:'a'});count+=1
    unknowns(check,m,('zby','zbn','zbo','eismu'))
    return dict(cases=count,initial_given_ruler_origin_and_role_axis_preserved=True,current_guide_and_distribution_bound=True)

@lru_cache(None)
def candidate_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    m|={'zbo':lambda f,role,ctx:'b' if role=='b' else 'a','zbn':lambda f,ctx:'a','eismu':lambda axis,f,ctx:'b'}
    args=['a','a','b',c(Q(-3)),'context',c(Q(3))]
    expected=('b','a','b','a','b','a','b','context','a','b',Q(-3),Q(3))
    check=lambda mm:run('eixh',args,mm,'instance');mm=m|{'eixg':lambda *xs:norm(xs)==expected}
    assert check(mm);count+=1
    assert not check(m|{'eixg':lambda *xs:False});count+=1
    # All existential individual slots have witnesses in a two-value domain.
    for i in range(len(expected)):
        wrong=tuple('wrong' if j==i else x for j,x in enumerate(expected))
        assert not check(m|{'eixg':lambda *xs:norm(xs)==wrong});count+=1
    for i in (4,8,9):
        changed=tuple(('a' if x=='b' else 'b') if j==i else x for j,x in enumerate(expected))
        assert check(m|{'eixg':lambda *xs:norm(xs)==changed});count+=1
    try:run('eixh',args[:-1],mm)
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('Real length witness silently enumerated')
    unknowns(check,mm,('eixg','zbo','zbn','eismu'))
    return dict(cases=count,two_value_domain_distinguishes_all_existential_slots=True,alternative_projection_observer_method_allowed=True,native_real_witness_not_finitely_enumerated=True)

@lru_cache(None)
def uniqueness_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;count=0
    norm=lambda xs:tuple(r(x) if isinstance(x,FunctionValue) else value(x) for x in xs)
    selected=('a','a','b',Q(-3),'context');args=['a','a','b','context']
    m['zcy']=lambda p,f,role,unit,ctx:c(Q(-3)) if (p,f,role,unit,ctx)==('a','a','b','a','context') else forbidden()
    for candidate,accepted in ((Q(-3),True),(Q(2),False),(Q(0),False)):
        rows={selected,('a','a','b',candidate,'context')}
        mm=m|{'eixh':lambda *xs:norm(xs) in rows}
        assert run('eixi',args+[c(candidate)],mm,'instance')==accepted;count+=1
    mm=m|{'eixh':lambda *xs:norm(xs)==selected}
    assert run('eixi',args+[c(Q(2))],mm,'instance');count+=1
    assert not run('eixi',args+[c(Q(2))],m|{'eixh':lambda *xs:False},'instance');count+=1
    for i in range(len(selected)):
        wrong=tuple('wrong' if j==i else x for j,x in enumerate(selected))
        assert not run('eixi',args+[c(Q(-3))],m|{'eixh':lambda *xs:norm(xs)==wrong},'instance');count+=1
    try:run('eixi',args,mm)
    except ValueError as e:assert 'Finite function domain' in str(e) or 'rational number domain' in str(e),str(e)
    else:raise AssertionError('All real coordinate values silently sampled')
    unknowns(lambda model:run('eixi',args+[c(Q(-3))],model,'instance'),mm,('eixh','zcy','sca'))
    return dict(cases=count,selected_candidate_exists_and_all_other_values_equal=True,full_real_uniqueness_not_finitely_sampled=True)

def source_record():
    old=json.loads(read(SOURCE_PARENT));validate_hashes(ROOT,old['source_sha256'])
    result=deepcopy(old);result.update(version='einstein-coordinate-measurement-source-reading-v1',reviewer='assistant_text_review_using_preserved_visual_collation')
    result['observations']+=['符号付き座標と非負の測定距離を分け、同じ原点・射影点・道具・方法へ結ぶ。','静止を個々の測定配置の期間として読む。全空間への統合には配置間の同じ対象・幾何・尺度の保持が必要。']
    result['remaining']=['同じ空間配置と対象を保つ各測定配置の接続と、両系の全空間・三成分への統合','時計配置点の局所時刻と§1の全信号試行による同期','二つの設定指示、表記と参照を含むu0045の全体統合・意味判断']
    paths=set(old['source_sha256'])|{SOURCE_PARENT,DOC}
    result['source_sha256']={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)};return result

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==270
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIOR));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[268,269])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/axis-projection-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));assert not doc['statements']
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=1,preserved_statements=270,prior_meanings_and_reviews_preserved=True,whole_unit_completion=False)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('magnitude',magnitude_checks),('instrument',instrument_checks),('procedure',procedure_checks),('projection',projection_checks),('identity',identity_checks),('candidate',candidate_checks),('uniqueness',uniqueness_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,PRIOR,*DEPENDENCIES,'scripts/compose_coordinate_measurement.py','scripts/check_coordinate_measurement.py','tests/test_coordinate_measurement.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_rod_methods.py','scripts/check_tau_differential.py','scripts/compose_axis_projection.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='calibrated_signed_coordinate_measurement_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=source['remaining'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
