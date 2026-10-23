"""Check affine frame motion, complete law comparisons, and definition roles."""
from functools import lru_cache
from itertools import product
from copy import deepcopy
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import DescriptionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,NUM
from scripts.compose_first_principle import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,INDEX,build
from scripts.review_first_principle import SOURCE,INVENTORY,DOC,PRIORS,source_record

DOMAIN=('a','b','c','d','e','f');POINTS=('now','other')

def forbidden(*args):raise ValueError('Unknown first-principle input')
def value(x):return json.loads(x.syntax)['symbol'] if isinstance(x,DescriptionValue) else x
def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


@lru_cache(None)
def fixture(name,mode='native'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    modes={'native':NUM,'frame_boundary':NUM|{'eioi'},'logic':{'eiok','eiom'},'unbounded':set()}
    abstract(doc,modes[mode])
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jfpc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jfpccontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jfpccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)];return doc,slots


def evaluate(doc,m,domain=DOMAIN):
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def run(name,args,m,mode='native'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jfpccontext':lambda:'now'}|{n:(lambda x=x:x) for n,x in zip(slots,args)})


def reject_unknown(check,m,symbols):
    for n in symbols:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown first-principle' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


@lru_cache(None)
def numeric_checks():
    cuts,m=arithmetic();count=0
    for speed,start,end,initial,error in product((-2,0,3),(1,4),(1,4),(-1,2),(0,1)):
        final=initial+speed*(end-start)+error
        assert run('eioh',[cuts.make(x) for x in (speed,start,end,initial,final)],m)==(error==0);count+=1
    args=[cuts.make(x) for x in (2,1,3,4,8)]
    for slot in range(5):
        bad=list(args);bad[slot]=cuts.make((2,1,3,4,8)[slot]+1)
        assert not run('eioh',bad,m);count+=1
    assert not run('eioh',args,m|{'ba':lambda x:cuts.read(x)!=Q(8)});count+=1
    reject_unknown(lambda x:run('eioh',args,x),m,('ba','bf','shv','sca'))
    try:run('eioh',args,m,'unbounded')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e)
    else:raise AssertionError('Unbounded real-cut arithmetic finitely enumerated')
    other,_=arithmetic()
    try:run('eioh',[other.make(2),*args[1:]],m)
    except ValueError as e:assert 'not constructed' in str(e)
    else:raise AssertionError('Unknown real representation decoded')
    return dict(cases=count,signed_and_zero_velocity=True,nonzero_coordinate_and_time_origins=True,exact_constructed_cut_oracle_not_sampling=True,unbounded_arithmetic_and_unknown_cuts_rejected=True)


def frame_model(mode='linear',speed=(-2,3,1)):
    cuts,m=arithmetic();make=cuts.make
    times=dict(zip(DOMAIN,(0,0,2,3,4,0)));axes=('a','b','c')
    offsets={'a':(0,0,0),'b':(2,1,0),'c':(0,0,0),'d':(0,0,0),'e':(0,0,3),'f':(0,0,0)}
    # Explicit total finite extensions support the eager evaluator outside the
    # selected point/time/axis sets. External unknown names still raise.
    time_table={(moment,frame,unit,ctx):make(times[moment]) for moment,frame,unit,ctx in product(DOMAIN,DOMAIN,DOMAIN,POINTS)}
    coord_table={}
    for point,moment,frame,unit,axis,ctx in product(DOMAIN,DOMAIN,DOMAIN,DOMAIN,DOMAIN,POINTS):
        i=axes.index(axis) if axis in axes else None;t=times[moment]
        val=0 if i is None else offsets[point][i]+speed[i]*t
        if mode=='accelerating' and i is not None:val+=t*t
        if mode=='rotating' and point=='b' and i==0:val+=t
        if mode=='origin_only' and point!='a' and i is not None:val=offsets[point][i]
        coord_table[point,moment,frame,unit,axis,ctx]=make(val)
    speeds={(first,second,lu,tu,axis,ctx):make(speed[axes.index(axis)] if axis in axes else 0) for first,second,lu,tu,axis,ctx in product(DOMAIN,DOMAIN,DOMAIN,DOMAIN,DOMAIN,POINTS)}
    def lookup(table):
        def call(*xs):
            if xs not in table:raise ValueError('Unknown first-principle input')
            return table[xs]
        return call
    points={'a','b','e'};moments={'c','d','e'}
    rows={'va':{('a',),('b',)},'ti':{('e',)},'ci':{('f',)},'eisk6':{('a','b','e','f','now')},'eislb':{('a','b','e','f','now')},'eisk7':{('b',p,'now') for p in points},'eisla':{('a','b',t,'now') for t in moments},'zce':{(p,t,'a','e','now') for p,t in product(points,moments)},'zcf':{(t,'a','f','now') for t in moments}}
    m.update({n:relation(rs) for n,rs in rows.items()})
    m.update(yn=lambda:'a',yo=lambda:'b',yp=lambda:'c',eisli=lambda f,s,c:'e',eislj=lambda f,s,c:'f',yl=lookup(time_table),ym=lookup(coord_table),eislc=lookup(speeds))
    return cuts,m,rows


@lru_cache(None)
def point_binding_checks():
    cuts,m,_=frame_model();args=['a','b','e','f','now','b','c','e'];count=0
    assert run('eioi',args,m);count+=1
    for symbol,arity in (('ym',6),('yl',4),('eislc',6)):
        # Each argument has an exact expected value at every native call.
        seen=[];original=m[symbol]
        def logged(*xs):seen.append(xs);return original(*xs)
        assert run('eioi',args,m|{symbol:logged});count+=1
        expected={'ym':{('b',t,'a','e',axis,'now') for t in ('c','e') for axis in ('a','b','c')},'yl':{(t,'a','f','now') for t in ('c','e')},'eislc':{('a','b','e','f',axis,'now') for axis in ('a','b','c')}}[symbol]
        assert set(seen)==expected
        target=sorted(expected)[-1]
        for slot in range(arity):
            def wrong(*xs,s=slot,target=target,original=original):
                # Distinguish every slot without a domain^arity enumeration.
                return cuts.make(cuts.read(original(*xs))+(1 if xs[s]==target[s] and xs==target else 0))
            assert not run('eioi',args,m|{symbol:wrong});count+=1
    reject_unknown(lambda x:run('eioi',args,x),m,('ym','yl','eislc'))
    return dict(cases=count,all_native_numeric_binding_slots_checked=True,three_components_share_same_point_time_pair_frames_and_units=True,unknown_inputs_rejected=3)


@lru_cache(None)
def frame_checks():
    count=0
    for mode,speed,expected in [('linear',(-2,3,1),True),('linear',(0,0,0),True),('linear',(2,-1,0),True),('accelerating',(-2,3,1),False),('rotating',(-2,3,1),False),('origin_only',(-2,3,1),False)]:
        _,m,_=frame_model(mode,speed);assert run('eiok',['a','b','now'],m)==expected;count+=1
    _,m,rows=frame_model()
    boundary=lambda x:run('eiok',['a','b','now'],x,'frame_boundary')
    m['eioi']=lambda f,s,lu,tu,c,p,start,end:(f,s,lu,tu,c)==('a','b','e','f','now')
    assert boundary(m);count+=1
    for symbol in rows:
        assert not boundary(m|{symbol:relation(set())});count+=1
    for symbol in ('eisk6','eislb'):
        row=next(iter(rows[symbol]))
        for i in range(len(row)):
            bad=tuple(('other' if isinstance(x,str) and x=='now' else 'f') if j==i else x for j,x in enumerate(row))
            if bad==row:bad=tuple('e' if j==i else x for j,x in enumerate(row))
            assert not boundary(m|{symbol:relation({bad})});count+=1
    for symbol in ('zce','zcf'):
        row=sorted(rows[symbol])[0]
        assert not boundary(m|{symbol:relation(rows[symbol]-{row})});count+=1
    assert not boundary(m|{'eisla':relation({('a','b','c','now')})});count+=1
    assert not boundary(m|{'yp':lambda:'a'});count+=1
    assert not boundary(m|{'eislj':lambda f,s,c:'e'});count+=1
    assert not run('eiok',['a','a','now'],m,'frame_boundary');count+=1
    assert not boundary(m|{'eioi':lambda f,s,lu,tu,c,p,start,end: not(p=='b' and start=='c' and end=='e')});count+=1
    reject_unknown(boundary,m,('eisk6','eislb','eisk7','eisla','zce','zcf','yl','eioi'))
    return dict(cases=count,all_configuration_points_and_moments_required=True,acceleration_rotation_and_origin_only_motion_rejected=True,zero_speed_and_unaligned_initial_positions_allowed=True,total_finite_fixture_extensions_not_unknown_fallbacks=True,unknown_inputs_rejected=8)


def law_model():
    rows={'eislg':{('d','now')},'eisle':{('d','e','now'),('d','f','now')},'eislf':{('d','a','now'),('d','b','now')},'eisld':{('c','now')},'vf':{('a','c','now'),('b','c','now')},'vh':{('a','a','c','now'),('a','b','d','now'),('b','a','e','now'),('b','b','f','now')},'vi':{('e','c','now'),('e','d','now'),('f','e','now'),('f','f','now')},'eisbi':{(law,frame,'now') for law,frame in product(('e','f'),('a','b'))}}
    return {n:relation(rs) for n,rs in rows.items()},rows


@lru_cache(None)
def law_checks():
    m,rows=law_model();check=lambda x:run('eiom',['a','b','d','now'],x);count=1;assert check(m)
    for symbol in ('eislg','eisle','eislf','eisld','vf','vh','eisbi'):
        assert not check(m|{symbol:relation(set())});count+=1
    for symbol in ('vf','vh','vi','eisbi'):
        for row in rows[symbol]:
            assert not check(m|{symbol:relation(rows[symbol]-{row})});count+=1
    # A representation of another history cannot fill a missing side.
    altered=(rows['vh']-{('b','b','f','now')})|{('a','b','f','now')}
    assert not check(m|{'vh':relation(altered)});count+=1
    assert not check(m|{'vh':relation(rows['vh']|{('a','b','e','now')})});count+=1
    # Rejected histories remain in scope, so changing one rejected side fails.
    assert not check(m|{'vi':relation(rows['vi']|{('e','f','now')})});count+=1
    assert check(m|{'vi':relation(set())});count+=1
    assert check(m|{'vi':relation({(law,r,'now') for law,r in product(('e','f'),DOMAIN)})});count+=1
    assert not check(m|{'eislf':relation(rows['eislf']|{('d','f','now')})});count+=1
    assert not check(m|{'eisle':relation(rows['eisle']|{('d','a','now')})});count+=1
    assert not check(m|{'eislg':relation({('d','other')})});count+=1
    reject_unknown(check,m,tuple(rows))
    # Native sap: all choices of two alternative representations on each side.
    for available in product((False,True),repeat=4):
        for admissible in product((False,True),repeat=4):
            reps=('c','d','e','f');left={x for x,on in zip(reps[:2],available[:2]) if on};right={x for x,on in zip(reps[2:],available[2:]) if on};allowed={x for x,on in zip(reps,admissible) if on}
            from noema.finite_semantics import FunctionValue
            represented=FunctionValue(('individual','individual','individual'),'truth',lambda h,f,r:h=='a' and r in (left if f=='a' else right if f=='b' else set()))
            conforms=FunctionValue(('individual','individual'),'truth',lambda l,r:l=='b' and r in allowed)
            expected=bool(left and right) and all((x in allowed)==(y in allowed) for x in left for y in right)
            assert run('sap',['a','a','b','b',represented,conforms],{})==expected;count+=1
    return dict(cases=count,all_laws_histories_and_representations=True,law_validity_distinct_from_candidate_admissibility=True,same_history_and_law_preserved=True,unknown_inputs_rejected=len(rows))


@lru_cache(None)
def scope_checks():
    # Small domain with two eligible directed pairs and no hidden choice of
    # a different theory per pair. Native eiom is checked separately above.
    pairs={('a','b','now'),('b','a','now')};m={'eiok':relation(pairs),'eiom':relation({(a,b,'c',t) for a,b,t in pairs})};count=1
    assert run('eion',[],m,'logic')
    assert not run('eion',[],m|{'eiok':relation(set())},'logic');count+=1
    assert not run('eion',[],m|{'eiom':relation({('a','b','c','now')})},'logic');count+=1
    assert not run('eion',[],m|{'eiom':relation({('a','b','c','now'),('b','a','d','now')})},'logic');count+=1
    assert not run('eion',[],m|{'eiok':relation(pairs|{('a','c','now')})},'logic');count+=1
    reject_unknown(lambda x:run('eion',[],x,'logic'),m,('eiok','eiom'))
    return dict(cases=count,one_theory_for_all_eligible_frame_pairs=True,nonempty_comparison_scope=True,unknown_inputs_rejected=2)


@lru_cache(None)
def presentation_checks():
    constants={'vk':'a','wu':'b','rd':'c','eirf':'d','wv':'e','eisk3':'f','ri':'now'};base={n:lambda x=x:x for n,x in constants.items()};count=0
    rows={'vl':{('a','c','eion','e','now')},'eislh':{('a','c','f','eifj','eion','d','now')}}
    m=base|{n:relation(rs) for n,rs in rows.items()}
    assert run('eioo',[],m);count+=1
    for symbol,rs in rows.items():
        row=next(iter(rs))
        for i in range(len(row)):
            bad=tuple('other' if j==i else x for j,x in enumerate(row))
            assert not run('eioo',[],m|{symbol:relation({bad})});count+=1
    reject_unknown(lambda x:run('eioo',[],x),m,tuple(rows))
    for path in (CORE,FULL):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        rows={'eir3':{('a','c','d','eiop','now')},'eislk':{('a','b',Q(1),'d','now')},'ue':{('b','a','now')}}
        m=base|{n:relation(rs) for n,rs in rows.items()}
        assert evaluate(doc,m);count+=1
        for symbol,rs in rows.items():
            row=next(iter(rs))
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not evaluate(doc,m|{symbol:relation({bad})});count+=1
        assert evaluate(doc,m|{n:forbidden for n in ('vl','eislh','eisk6','eislg','vh','vi','eisbi')});count+=1
        reject_unknown(lambda x:evaluate(doc,x),m,tuple(rows))
    return dict(cases=count,first_numbered_definition_and_antecedent_reference=True,physical_principle_not_executed_by_quotation=True,unknown_inputs_rejected=8)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==250
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([248],[213,214,215,216])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert prior['selection']==selection_binding(new,indices)
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/second-section-opening-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert {'sar','saq','sap','sbn','eifj','eisbi'}<=set(ds)
    assert not {'vb','vc','vg','saw'}&set(ds)
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=249,earlier_judgments_preserved=True,whole_226_character_source_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('numeric',numeric_checks),('point_bindings',point_binding_checks),('frames',frame_checks),('laws',law_checks),('scope',scope_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    s=source_record()['segments'][0]
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source_record()['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,'scripts/compose_first_principle.py','scripts/check_first_principle.py','scripts/review_first_principle.py','tests/test_first_principle.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='first_principle_uniform_translation_and_law_preservation_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation')]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['全単位判断の登録、第二原理u0026以降'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
