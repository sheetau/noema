"""Check stationary representatives and scoped, non-factive observer responses."""
from functools import lru_cache
from fractions import Fraction as Q
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_moving_trip_geometry import NUM,numbers,norm_factory
from scripts.check_material_relative_frame import RS
from scripts.check_rod_methods import value,relation
from scripts.compose_observer_contrast import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDEX,MEANINGS,PRIMITIVES,build
from scripts.review_observer_contrast import DOC,SOURCE,INVENTORY,PRIORS,DEPENDENCIES,source_record

DOMAIN=('observera','observerb','observerc','other','firstend','lastend','carrieda','carriedb','rod','frame','lengthunit','timeunit','x','y','z','author','paper','scope','resultnode','contrastnode','lengthname')
POINTS=('context','measurement','discourse','other')
def forbidden(*xs):raise ValueError('Unknown observer-contrast input')
def constants():return {n:lambda x=x:x for n,x in {'yd':'context','xi':'rod','xn':'firstend','xo':'lastend','zaj':'carrieda','zak':'carriedb','zay':'observera','zaz':'observerb','ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'x','yo':'y','yp':'z','rd':'author','eirf':'paper','ri':'discourse','xy':'scope','za3':'resultnode','zbb':'contrastnode','eismn':'lengthname'}.items()}

@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    boundaries=NUM|{'eiq4','eitm','eip6','eiqg'}
    if mode!='native_history':boundaries.add('se')
    if name!='eit2':boundaries.add('eit2')
    if name!='eit3':boundaries.add('eit3')
    abstract(doc,boundaries);doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='joc'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    expr=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='joccontext',parameters=[],result='situation'));expr=dict(kind='evaluate',content=expr,situation=dict(kind='call',symbol='joccontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=expr)];return doc,slots

def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm=constants()|m|{n:lambda x=x:x for n,x in zip(slots,args)};mm.setdefault('joccontext',lambda:'discourse')
    return evaluate_document(doc,individuals=DOMAIN,situations=POINTS,primitives={d['name']:mm.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=300000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown observer-contrast' in str(e),str(e)
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
def rest_checks():
    cuts,m=numbers();c=cuts.make;r=cuts.read;norm=norm_factory(cuts,(0,1,2));count=0
    m['zzbg']=lambda a,b:r(a)<r(b)
    def traces(profile):
        return [FunctionValue((RS,),RS,lambda t,a=a:c(Q(4+a)+(r(t) if profile=='drift' and a==1 else r(t)*(2-r(t)) if profile=='return' and a==2 else 0))) for a in range(3)]
    shared=['observera','frame','context','lengthunit','timeunit',c(Q(0)),c(Q(2))]
    for profile in ('rest','drift','return'):
        args=shared+traces(profile);row=norm(args)
        model=m|{'se':lambda *xs,row=row:norm(xs)==row,'eisdd':lambda *xs:xs==('frame','lengthunit','timeunit','context')}
        assert run('eit2',args,model)==(profile=='rest');count+=1
    args=shared+traces('rest');rows={'se':{norm(args)},'eisdd':{('frame','lengthunit','timeunit','context')}}
    model=m|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda mm:run('eit2',args,mm),model,rows,norm)
    for slot in range(len(args)):
        bad=list(args)
        if slot in (5,6):bad[slot]=c(Q(9))
        elif slot>=7:bad[slot]=FunctionValue((RS,),RS,lambda t:c(Q(9)))
        else:bad[slot]='other'
        assert not run('eit2',bad,model);count+=1
    for lower,upper in ((0,0),(2,0)):
        bad=list(args);bad[5:7]=[c(Q(lower)),c(Q(upper))]
        assert not run('eit2',bad,model|{'se':lambda *xs:True});count+=1
    unknowns(lambda mm:run('eit2',args,mm),model,('ba','bf','bd','shv','bg'))
    try:run('eit2',args,model,'native_history')
    except ValueError as e:assert 'rational number domain' in str(e) or 'Finite function domain' in str(e),str(e)
    else:raise AssertionError('Complete real history replaced with finite samples')
    rows={'eit2':{norm(args)},'xb':{('observera',)},'x4':{('observera','frame','context')}}
    fs=traces('rest')
    def selector(who,frame,lu,tu,axis,ctx):
        if (who,frame,lu,tu,ctx)!=('observera','frame','lengthunit','timeunit','context') or axis not in ('x','y','z'):forbidden()
        return fs[('x','y','z').index(axis)]
    mm=m|{'eisls':lambda *xs:c(Q(0)),'eislt':lambda *xs:c(Q(2)),'eismh':selector}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count+=perturb(lambda model:run('eit3',['observera','context'],model),mm,rows,norm)
    unknowns(lambda model:run('eit3',['observera','context'],model),mm,('eisls','eislt','eismh'))
    return dict(cases=count,stationary_representative_uses_two_complete_histories=True,interior_return_motion_not_stationary=True,same_frame_units_interval_and_position_functions=True,full_real_history_refused=True,finite_boundary_samples_not_proof_of_all_times=True)

@lru_cache(None)
def quantity_checks():
    cuts,m=numbers();c=cuts.make;norm=norm_factory(cuts,(0,1));rows={'yx':{('context','measurement')},'eiqg':{(Q(6),'measurement')},'eip6':{(Q(6),'measurement')}}
    m|={'zav':lambda:c(Q(6))}|{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}
    count=perturb(lambda mm:run('eit4',['rod',c(Q(6)),'measurement'],mm),m,rows,norm)
    for rod,val,ctx in (('other',6,'measurement'),('rod',7,'measurement'),('rod',6,'other')):
        assert not run('eit4',[rod,c(Q(val)),ctx],m);count+=1
    assert not run('eit4',['rod',c(Q(6)),'measurement'],m|{'zav':lambda:c(Q(7))});count+=1
    unknowns(lambda mm:run('eit4',['rod',c(Q(6)),'measurement'],mm),m,('zav','sca'))
    return dict(cases=count,same_rod_current_rest_frame_measurement_and_zav=True)

@lru_cache(None)
def judgment_checks():
    rows={'eitm':{('context',)},'zba':{(o,'sdo',False,'context') for o in ('observera','observerb')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiub',['context'],mm),m,rows)
    assert run('eiub',['context'],m|{n:forbidden for n in ('bi','zag','sdo','eiq4')});count+=1
    rows={'eit3':{('observera','context'),('observerb','context')},'zba':{(o,'eit6',True,'context') for o in ('observera','observerb')},'eisfd':{(o,'eit6','paper','context') for o in ('observera','observerb')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiua',['context'],mm),m,{n:rows[n] for n in ('zba','eisfd')})
    assert not run('eiua',['context'],m|{'eit3':lambda *xs:False});count+=1
    assert not run('eiua',['context'],m|{'eit3':relation(rows['eit3']|{('observerc','context')})});count+=1
    assert run('eiua',['context'],m|{'eit3':relation({('observera','context')})});count+=1
    assert run('eiua',['context'],m|{n:forbidden for n in ('eiq4','bi','ce','se')});count+=1
    unknowns(lambda mm:run('eiua',['context'],mm),m,('eit3','zba','eisfd'))
    # The two clock qualifications are native calls inside the positive content;
    # judging that content does not evaluate them.
    rows={'eiq4':{('carrieda','firstend','context'),('carriedb','lastend','context')}}
    m={'joccontext':lambda:'context',**{n:relation(rs) for n,rs in rows.items()}}
    count+=perturb(lambda mm:run('eit6',[],mm),m,rows)
    return dict(cases=count,explicit_negative_judgment_not_absence_of_positive=True,same_two_comoving_observers_and_midpoint_content=True,nonempty_stationary_scope_and_all_selected_observers=True,positive_declaration_distinct_from_private_judgment=True,judgment_contents_not_executed_or_assumed_true=True,current_complete_clock_qualification_bound=True)

@lru_cache(None)
def presentation_checks():
    rows={'eislo':{('lengthname','eit4','paper','discourse')},'eisa5':{('contrastnode','author','eitp','eit5','discourse')},'uh':{('contrastnode','author','eiue','scope','discourse')},'eisdk':{('paper','eitp','eiue','discourse')},'zbc':{('contrastnode','author','eiuc','eiud','scope','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count=perturb(lambda mm:run('eiuf',[],mm),m,rows)
    assert run('eiuf',[],m|{n:forbidden for n in ('eitp','eit4','eiua','eiub','zba','eisfd','se')});count+=1
    rows={'eir3':{('contrastnode','author','paper','eiug','discourse')},'ue':{('resultnode','contrastnode','discourse')}}
    m={n:relation(rs) for n,rs in rows.items()};count+=perturb(lambda mm:run('eiuh',[],mm),m,rows)
    assert run('eiuh',[],m|{n:forbidden for n in ('uh','zbc','eisdk','eislo')});count+=1
    return dict(cases=count,hypothetical_scope_reason_and_ordered_contrast=True,length_gloss_supplements_same_previous_result=True,author_attribution_does_not_execute_judgments=True)

@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==265
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for p,indices in zip(PRIORS,([261,262,263],[263])):
        prior=json.loads(read(p));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,indices)==prior['selection']
    for p in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(p))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries'][:-1]==json.loads(read('data/moving-trip-reading-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']};assert len(doc['statements'])==1
    assert ds['eiug']['body']['force']=='assert' and ds['eiug']['body']['content']['symbol']=='eiuf'
    for style in ('compact','full'):
        body=format_graph(doc,style);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
    assert json.loads(read(SOURCE))==source_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_statements=264,prior_meanings_and_reviews_preserved=True)

def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')

@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('rest',rest_checks),('quantity',quantity_checks),('judgments',judgment_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_observer_contrast.py','scripts/check_observer_contrast.py','scripts/review_observer_contrast.py','tests/test_observer_contrast.py','scripts/check_moving_trip_geometry.py','scripts/check_coordinate_correspondence.py','scripts/check_rod_methods.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_moving_trip_geometry.py','scripts/compose_rod_methods.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='rest_frame_length_and_observer_contrast_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0040の全単位判断登録','u0041以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
