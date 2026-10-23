"""Check physical four-tuples, same-event direction and heading topic roles."""
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_rod_methods import value,relation
from scripts.compose_transformation_heading import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build
from scripts.review_transformation_heading import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=('event','tuple','frame','moving','lengthunit','timeunit','x','y','z','time','inquiry','node','section','part','paper','previous','other')
POINTS=('context','discourse','other');SMALL=('zero','one')
def forbidden(*xs):raise ValueError('Unknown transformation-heading input')
def constants():return {n:lambda x=x:x for n,x in {'ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','zc7':'time','eismt':'node','eisms':'section','eisdx':'part','eirf':'paper','zbk':'previous','ri':'discourse'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eiuk'}
    if mode!='native_uniqueness':boundaries.add('sd')
    if name=='eiu2':boundaries|={'eiuz','eiuo'}
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jth'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=name,arguments=args))];return doc,slots

def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    return evaluate_document(doc,individuals=domain,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown transformation-heading' in str(e),str(e)
        else:raise AssertionError(('Unknown input accepted',n))

def perturb(check,m,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs}),(n,row);count+=1
            for i in range(len(row)):
                changed=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:lambda *xs,rs=(rs-{row})|{changed}:norm(xs) in rs}),(n,i);count+=1
    unknowns(check,m,rows);return count

@lru_cache(None)
def assignment_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,())
    components={'x':Q(2),'y':Q(-3),'z':Q(4),'time':Q(7)}
    def component(tup,axis):
        if tup!='tuple' or axis not in components:forbidden()
        return c(components[axis])
    def stamp(e,f,u,ctx):
        if (e,f,u,ctx)!=('event','frame','timeunit','context'):forbidden()
        return c(Q(7))
    rows={'zbd':{('event',)},'va':{('frame',)},'ti':{('lengthunit',)},'ci':{('timeunit',)},'zc5':{('tuple',)},'eisdd':{('frame','lengthunit','timeunit','context')},'sd':{('frame','context','lengthunit','timeunit')},'eiuk':{('event','frame','timeunit','context')},'zzbu':{('event','frame','context','lengthunit','timeunit',Q(7),Q(2),Q(-3),Q(4))}}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()};m|={'zc6':component,'zbe':stamp}
    check=lambda mm:run('eiuz',['event','tuple','frame','context'],mm)
    count=perturb(check,m,rows,norm)
    for axis in components:
        changed=lambda tup,a,axis=axis:c(components[a]+(1 if a==axis else 0))
        assert not check(m|{'zc6':changed});count+=1
    assert not check(m|{'zbe':lambda *xs:c(Q(8))});count+=1
    for name in ('ba','zzba'):
        assert not check(m|{name:lambda x:False});count+=1
    # If only the local-clock time differs, numeric equality still rejects it.
    assert not check(m|{'sca':lambda a,b:False});count+=1
    for a,b in (('yn','yo'),('yn','yp'),('yn','zc7'),('yo','yp'),('yo','zc7'),('yp','zc7')):
        assert not check(m|{a:constants()[b]});count+=1
    # Distinct length/time units remain a structural requirement even if all
    # boundary relations accept the collision.
    yes={n:lambda *xs:True for n in rows};yes|={'zbe':lambda *xs:c(Q(7))}
    assert not check(m|yes|{'rb':lambda:'lengthunit'});count+=1
    unknowns(check,m,('zc6','zbe','ba','zzba','sca'))
    try:run('eiuz',['event','tuple','frame','context'],m,'native_uniqueness')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete coordinate uniqueness silently sampled')
    return dict(cases=count,three_coordinates_and_time_same_event_units_and_frame=True,native_sha_and_sa_with_current_eiuk_boundary=True,all_real_coordinate_uniqueness_preserved_and_refused=True,unknown_components_not_zero=True)

@lru_cache(None)
def correspondence_checks():
    args=['zero','one','zero','one','context'];count=0
    base={'eiuo':relation({('zero','one','context')}),'zbd':lambda e:True}
    # With only two carrier values, distinguish every source/target witness.
    for source,target in product(SMALL,repeat=2):
        rows={(source,'zero','zero','context'),(target,'one','one','context')}
        model=base|{'eiuz':relation(rows)}
        assert run('eiu2',args,model,domain=SMALL)==(source==target);count+=1
    rows={'eiuo':{('zero','one','context')},'zbd':{('zero',)},'eiuz':{('zero','zero','zero','context'),('zero','one','one','context')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiu2',args,mm,domain=SMALL),m,rows)
    for slot in range(5):
        bad=list(args);bad[slot]='other' if slot==4 else ('one' if bad[slot]=='zero' else 'zero')
        assert not run('eiu2',bad,m,domain=SMALL);count+=1
    assert not run('eiu2',args,m|{'eiuz':relation({('zero','zero','one','context'),('zero','one','zero','context')})},domain=SMALL);count+=1
    assert not run('eiu2',args,m|{'eiuz':lambda *xs:False},domain=SMALL);count+=1
    return dict(cases=count,same_event_witness_not_two_different_events=True,source_and_target_direction_and_all_argument_slots=True,current_nonzero_uniform_motion_and_assignments_bound=True)

@lru_cache(None)
def topic_checks():
    rows={'eismr':{('inquiry','eiu2','context')}};m={'eismr':relation(rows['eismr'])}
    count=perturb(lambda mm:run('eiu3',['inquiry','context'],mm),m,rows)
    assert run('eiu3',['inquiry','context'],m|{n:forbidden for n in ('eiuo','eiuz','eiuk','zc6','zzbu','sd')});count+=1
    return dict(cases=count,directed_correspondence_is_theory_subject=True,no_formula_discovery_or_physical_model_execution_implied=True)

@lru_cache(None)
def heading_checks():
    rows={'eisdv':{('node','section','part','paper',Q(2),Q(3),'discourse')},'eisdw':{('node','section','eiu3','discourse')},'ue':{('previous','node','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiu4',[],mm),m,rows)
    for n,x in (('eismt','section'),('eisms','part'),('zbk','node')):
        assert not run('eiu4',[],m|{p:lambda *xs:True for p in rows}|{n:lambda x=x:x});count+=1
    assert run('eiu4',[],m|{n:forbidden for n in ('eismr','eiuo','eiuz','eiuk','zc6','zzbu','sd')});count+=1
    for path in (FULL,CORE):
        doc=parse(read(path));doc['statements']=[doc['statements'][-1]];mm=constants()|m
        assert evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value'];count+=1
    return dict(cases=count,section_three_depth_two_parent_part_one=True,preceding_conclusion_order_and_distinct_nodes=True,full_and_core_heading_not_physical_assertions=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==267
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=json.loads(read(PRIORS[0]));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[265])==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/simultaneity-conclusion-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==1
    assert {'eiuk','eiuo','sd','sa','sgu','sha','eihq'}<=set(ds)
    assert not {'eir3','uh','eisdk'}&set(ds)
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=266,prior_meanings_and_reviews_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('assignments',assignment_checks),('correspondence',correspondence_checks),('topic',topic_checks),('heading',heading_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_transformation_heading.py','scripts/check_transformation_heading.py','scripts/review_transformation_heading.py','tests/test_transformation_heading.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_simultaneity_conclusion.py','scripts/compose_material_relative_frame.py','scripts/compose_limits.py'}
    return dict(status='directed_space_time_transformation_heading_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0042の全単位判断登録','u0043以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
