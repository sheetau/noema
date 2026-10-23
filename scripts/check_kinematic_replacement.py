"""Check full coordinate images, physical configuration bindings and attribution."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction as Q
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.extraction import extract_document
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,RS,FS
from scripts.check_rod_methods import value,relation,NUM
from scripts.check_rod_length_claims import replace_real_sort
from scripts.compose_kinematic_replacement import ROOT,read,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,INDICES,MEANINGS,build
from scripts.review_kinematic_replacement import SOURCE,DOC,INVENTORY,PRIORS,DEPENDENCIES,source_record

POINTS=('p','q','r');DOMAIN=POINTS+('body','otherbody','frame','lengthunit','timeunit','xaxis','yaxis','zaxis','author','paper','scope','kinematics','assumptionnode','rewording','forecast','other')
SITUATIONS=('moving','resting','alternative','context');HISTORY={'eiag','eiah','eigy'}
def forbidden(*xs):raise ValueError('Unknown kinematic-replacement input')
def constants():return {n:lambda x=x:x for n,x in {'ra':'frame','ta':'lengthunit','rb':'timeunit','yn':'xaxis','yo':'yaxis','yp':'zaxis','rd':'author','eirf':'paper','xy':'scope','ri':'context','yd':'moving','zr':'kinematics','zv':'assumptionnode','zw':'rewording','zh':'forecast','ye':'moving','yf':'resting'}.items()}


@lru_cache(None)
def fixture(name,mode='boundary'):
    doc=extract_document(parse(read(CORE)),roots=[name],statement_indices=[]).document
    names=NUM|HISTORY
    if name=='eiqv':names|={'eip2','eip6','sbg'}
    if mode=='scope':names|={'eiqs'}
    if mode=='binding':names|={'eiqr'}
    if mode!='full':abstract(doc,names)
    doc=extract_document(doc,roots=[name],statement_indices=[]).document
    d=next(d for d in doc['declarations'] if d['name']==name);slots=[];args=[]
    for i,p in enumerate(d['parameters']):
        n='jkrep'+number_word(i);slots.append(n);doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']));args.append(dict(kind='call',symbol=n,arguments=[]))
    body=dict(kind='call',symbol=name,arguments=args)
    if d['result']=='content':
        doc['declarations'].append(dict(kind='primitive',name='jkrepcontext',parameters=[],result='situation'));body=dict(kind='evaluate',content=body,situation=dict(kind='call',symbol='jkrepcontext',arguments=[]))
    doc['statements']=[dict(kind='ask',body=body)]
    return doc,slots


def evaluate(doc,m,domain=DOMAIN):return evaluate_document(doc,individuals=domain,situations=SITUATIONS,primitives={d['name']:m.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1000000,memoize_definitions=True,memoize_expressions=True)[0]['value']
def run(name,args,m,mode='boundary',domain=DOMAIN):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    return evaluate(doc,m|{'jkrepcontext':lambda:'context'}|{n:(lambda x=x:x) for n,x in zip(slots,args)},domain)
def unknowns(check,m,names):
    for n in names:
        try:check(m|{n:forbidden})
        except ValueError as e:assert 'Unknown kinematic-replacement' in str(e)
        else:raise AssertionError(('Unknown input accepted',n))


def families(cuts,positions,velocity=0):
    def at(axis,p,t):
        if p not in positions:forbidden()
        return cuts.make(Q(positions[p][axis])+(cuts.read(t)-7)*velocity*(axis==0))
    return [FunctionValue(('individual',),FS,lambda p,i=i:FunctionValue((RS,),RS,lambda t:at(i,p,t))) for i in range(3)]
def member(selected):return FunctionValue(('individual',),'truth',lambda p:p in selected)


@lru_cache(None)
def snapshot_checks():
    cuts,m=arithmetic();c=cuts.make;count=0
    first={'p':(0,0,0),'q':(2,0,0),'r':(1,1,0)}
    scenarios={
      'identical':(first,True),
      'same_endpoints_hidden_deformation':(first|{'r':(1,0,0)},False),
      'same_xy_different_depth':(first|{'r':(1,1,1)},False),
      'swapped_material_labels':({'p':first['q'],'q':first['p'],'r':first['r']},True),
      'translated_congruent_shape':({p:(x+3,y,z) for p,(x,y,z) in first.items()},False),
      'rotated_congruent_shape':({p:(-y,x,z) for p,(x,y,z) in first.items()},False),
    }
    for label,(second,expected) in scenarios.items():
        args=[member(POINTS),member(POINTS),c(Q(7)),*families(cuts,first),*families(cuts,second)]
        assert run('eiqr',args,m,domain=POINTS)==expected,label;count+=1
    # Exhaustive subset pairs check both inclusions, extra points and nonemptiness.
    for a,b in product(product((False,True),repeat=3),repeat=2):
        left={p for p,yes in zip(POINTS,a) if yes};right={p for p,yes in zip(POINTS,b) if yes}
        args=[member(left),member(right),c(Q(7)),*families(cuts,first),*families(cuts,first)]
        assert run('eiqr',args,m,domain=POINTS)==(bool(left) and left==right);count+=1
    duplicate_first={'p':(0,0,0),'q':(2,0,0),'r':(0,0,0)};duplicate_second=duplicate_first|{'r':(2,0,0)}
    assert run('eiqr',[member(POINTS),member(POINTS),c(Q(7)),*families(cuts,duplicate_first),*families(cuts,duplicate_second)],m,domain=POINTS);count+=1
    for time,expected in ((7,True),(8,False)):
        assert run('eiqr',[member(POINTS),member(POINTS),c(Q(time)),*families(cuts,first,velocity=1),*families(cuts,first)],m,domain=POINTS)==expected;count+=1
    unknown=FunctionValue(('number',),'truth',lambda x:x<7)
    try:run('eiqr',[member(POINTS),member(POINTS),unknown,*families(cuts,first),*families(cuts,first)],m,domain=POINTS)
    except ValueError:pass
    else:raise AssertionError('Unknown time decoded by probing')
    return dict(cases=count,complete_coordinate_images_compared_both_directions=True,interior_and_transverse_shape_changes_detected=True,material_labels_and_multiplicity_not_geometry=True,same_shape_at_other_place_or_time_not_accepted=True)


def setup():
    cuts,m=arithmetic();c=cuts.make;r=cuts.read;m|=constants();m|={'bg':lambda a,b:r(a)<r(b),'va':lambda f:f=='frame','ti':lambda u:u=='lengthunit','ci':lambda u:u=='timeunit'}
    positions={p:(Q(20+i),Q(3),Q(1)) for i,p in enumerate(DOMAIN)}|{'p':(Q(0),Q(0),Q(0)),'q':(Q(2),Q(0),Q(0)),'r':(Q(1),Q(1),Q(0))}
    fs={ctx:families(cuts,positions,velocity=1 if ctx=='moving' else 0) for ctx in SITUATIONS}
    bounds={'moving':(6,8),'resting':(5,9),'alternative':(6,8),'context':(6,8)}
    def family(body,frame,lu,tu,axis,ctx):
        if body not in ('body','otherbody') or (frame,lu,tu)!=('frame','lengthunit','timeunit') or axis not in ('xaxis','yaxis','zaxis') or ctx not in fs:forbidden()
        return fs[ctx][('xaxis','yaxis','zaxis').index(axis)]
    def bound(frame,tu,ctx,i):
        if (frame,tu)!=('frame','timeunit') or ctx not in bounds:forbidden()
        return c(Q(bounds[ctx][i]))
    m|={'eirh':lambda b,p,ctx:b=='body' and p in POINTS and ctx in SITUATIONS,'eislu':family,'eisls':lambda f,u,ctx:bound(f,u,ctx,0),'eislt':lambda f,u,ctx:bound(f,u,ctx,1),'zl':lambda b,mov,rest:(b,mov,rest)==('body','moving','resting')}
    def norm(xs):
        def one(x):
            if not isinstance(x,FunctionValue):return value(x)
            if x.parameters==('number',):return r(x)
            if x.result=='truth':return tuple(p for p in DOMAIN if x(p))
            if x.result==FS:return tuple(r(x(p)(c(Q(t)))) for p in DOMAIN for t in (7,8))
            forbidden()
        return tuple(one(x) for x in xs)
    def history(ctx):return ('body','frame',ctx,'lengthunit','timeunit',*map(Q,bounds[ctx]),POINTS,*(tuple(r(f(p)(c(Q(t)))) for p in DOMAIN for t in (7,8)) for f in fs[ctx]))
    expected={'eiag':{history('moving')},'eiah':{history('resting')},'eigy':{history('moving'),history('resting')}}
    expected['eiqr']={norm([member(POINTS),member(POINTS),c(Q(7)),*fs['moving'],*fs['resting']])}
    m|={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in expected.items()}
    return cuts,m,expected,norm


@lru_cache(None)
def configuration_checks():
    cuts,m,expected,norm=setup();c=cuts.make;count=0
    args=['body','moving','resting',c(Q(7))];check=lambda mm:run('eiqs',args,mm)
    assert check(m);count+=1
    # The native image comparison is checked above and once with these histories.
    # Binding mutations use an explicit boundary for it to avoid repeating its
    # quadratic point search while changing unrelated history fields.
    binding=lambda mm:run('eiqs',args,mm,mode='binding')
    for n,rs in expected.items():
        for row in rs:
            assert not binding(m|{n:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not binding(m|{n:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    for n in ('zl','va','ti','ci'):
        assert not binding(m|{n:lambda *xs:False});count+=1
    # Keep image boundary fixed for the guards, with all physical history inputs known.
    for time in (4,9):assert not run('eiqs',['body','moving','resting',c(Q(time))],m|{'eiqr':lambda *xs:True},mode='binding');count+=1
    for lower,upper in ((7,7),(8,6)):
        mm=m|{'eisls':lambda *xs:c(Q(lower)),'eislt':lambda *xs:c(Q(upper)),**{n:lambda *xs:True for n in HISTORY},'eiqr':lambda *xs:True}
        assert not run('eiqs',args,mm,mode='binding');count+=1
    mm=m|{n:lambda *xs:True for n in HISTORY|{'zl','eiqr'}}
    assert not run('eiqs',['body','moving','moving',c(Q(7))],mm,mode='binding');count+=1
    mm|={'eirh':lambda b,p,ctx:b=='body' and p in (('p','q') if ctx=='resting' else POINTS)}
    assert not run('eiqs',args,mm,mode='binding');count+=1
    unknowns(binding,m,('eiag','eiah','eigy','zl','eirh','eislu','eisls','eislt'))
    assert check(m|{'xv':forbidden,'ya':forbidden,'zk':forbidden,'zo':forbidden,'zq':forbidden});count+=1
    # At native boundary an unknown physical input never becomes a false default.
    unknowns(check,m,('zl','eislu'))
    return dict(cases=count,complete_moving_and_resting_rigid_histories_bound=True,same_material_members_and_admissible_configuration_required=True,epoch_inside_both_positive_intervals=True,old_unexpanded_occupancy_and_rigidity_not_used=True)


@lru_cache(None)
def scope_checks():
    cuts,m=arithmetic();c=cuts.make;m|=constants();m['zp']=lambda:c(Q(7));count=0
    chosen=('body','otherbody')
    for mask in product((False,True),repeat=2):
        targets={b for b,yes in zip(chosen,mask) if yes}
        for supported in (set(),{'body'},{'otherbody'},set(chosen)):
            model=m|{'zn':lambda b,ctx:ctx=='moving' and b in targets,'eiqs':lambda b,mov,rest,t:b in supported and mov=='moving' and rest=='resting' and cuts.read(t)==7}
            assert run('eiqu',[],model,mode='scope')==(bool(targets) and targets<=supported);count+=1
    for resting in ('resting','alternative'):
        model=m|{'eiqs':lambda b,mov,rest,t:(b,mov,rest,cuts.read(t))==('body','moving',resting,Q(7))}
        assert run('eiqt',['body','moving',c(Q(7))],model,mode='scope');count+=1
    unknowns(lambda mm:run('eiqu',[],mm,mode='scope'),m|{'zn':lambda b,ctx:b=='body','eiqs':lambda *xs:True},('zn','eiqs','zp'))
    return dict(cases=count,nonempty_full_selected_body_range_and_every_body_checked=True,at_least_one_rest_configuration_not_unique=True,epoch_not_identified_with_prior_measurement_time=True)


@lru_cache(None)
def length_checks():
    domain=('base','alias','different');numbers={'base':5,'alias':5,'different':4};doc=replace_real_sort(deepcopy(fixture('eiqv')[0]));count=0
    for first_bits,second_bits in product(product((False,True),repeat=3),repeat=2):
        first={p for p,b in zip(domain,first_bits) if b};second={p for p,b in zip(domain,second_bits) if b}
        a={numbers[x] for x in first};b={numbers[x] for x in second}
        m=constants()|{'jkrepcontext':lambda:'context','eip2':lambda v,ctx:ctx=='moving' and v in first,'eip6':lambda v,ctx:ctx=='resting' and v in second,'sbg':lambda v:True,'sca':lambda a,b:numbers[a]==numbers[b]}
        assert evaluate(doc,m,domain)==(len(a)==len(b)==1 and a==b);count+=1
    cuts,m=arithmetic();m|=constants()
    try:run('eiqv',[],m)
    except ValueError as e:assert 'Cannot finitely quantify the rational number domain' in str(e)
    else:raise AssertionError('Real-cut domain silently sampled')
    return dict(cases=count,two_method_values_not_initial_length_compared=True,nonempty_and_value_unique_results_required=True,same_value_aliases_allowed=True,projection_only_and_full_real_domain_refused=True)


def perturb(check,m,rows):
    count=1;assert check(m)
    for n,rs in rows.items():
        for row in rs:
            assert not check(m|{n:relation(rs-{row})});count+=1
            for i in range(len(row)):
                bad=tuple('other' if j==i else x for j,x in enumerate(row))
                assert not check(m|{n:relation((rs-{row})|{bad})});count+=1
    unknowns(check,m,rows);return count


@lru_cache(None)
def presentation_checks():
    rows={'zs':{('kinematics','context')},'zt':{('kinematics',a,'scope','context') for a in ('eiqv','eiqu')},'zx':{('rewording','author','kinematics','eiqv','eiqu','scope','context')}}
    m=constants()|{n:relation(rs) for n,rs in rows.items()}|{'zu':lambda *xs:False}
    count=perturb(lambda mm:run('eiqw',[],mm),m,rows)
    for assumption in ('eiqv','eiqu'):
        assert not run('eiqw',[],m|{'zu':relation({('kinematics',assumption,'scope','context')})});count+=1
    # Unknown explicitness is not evidence that the assumption is tacit.
    unknowns(lambda mm:run('eiqw',[],mm),m,('zu',))
    assert run('eiqw',[],m|{n:forbidden for n in ('eip2','eip6','eirh','eislu','zl','zp','ya','xv')});count+=1
    for path in (FULL,CORE):
        doc=parse(read(path));doc['statements']=doc['statements'][-1:]
        rows={'eir3':{('assumptionnode','author','paper','eiqx','context')},'ue':{('forecast','assumptionnode','context')}}
        m=constants()|{n:relation(rs) for n,rs in rows.items()}
        count+=perturb(lambda mm:evaluate(doc,mm),m,rows)
        assert evaluate(doc,m|{n:forbidden for n in ('zs','zt','zu','zx','eirh','eislu','zl')});count+=1
    return dict(cases=count,used_and_not_explicit_both_required=True,unknown_explicitness_not_negated=True,author_reformulation_not_logical_equivalence=True,quotation_not_author_agreement_or_physical_execution=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==260
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    for path,index in zip(PRIORS,(257,258)):
        prior=json.loads(read(path));validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[index])==prior['selection']
    for path in DEPENDENCIES:validate_hashes(ROOT,json.loads(read(path))['source_sha256'])
    load_annotations(ROOT,BASIS,ANNOTATIONS);assert json.loads(read(ANNOTATIONS))['entries']==json.loads(read('data/rod-length-claims-identifiers-v1.json'))['entries']
    doc=parse(read(CORE));ds={d['name']:d for d in doc['declarations']}
    assert {'eiad','eiag','eiah','eigy','eisdd','sck','scj','eip2','eip6'}<=set(ds)
    assert not {'zk','zo','zq','scm'}&set(ds)
    assert ds['eiqx']['body']['force']=='assert' and ds['eiqx']['body']['content']['symbol']=='eiqw'
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    source=json.loads(read(SOURCE));assert source==source_record();validate_hashes(ROOT,source['source_sha256'])
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=259,prior_length_claims_and_meanings_preserved=True,whole_original_sentence_and_t_checked=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/SOURCE,json.dumps(source_record(),ensure_ascii=False,indent=2)+'\n')


@lru_cache(None)
def build_report():
    results={n:fn() for n,fn in [('snapshot',snapshot_checks),('configuration',configuration_checks),('scope',scope_checks),('length',length_checks),('presentation',presentation_checks),('structure',structure_checks)]}
    source=source_record();paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|set(source['source_sha256'])|{SOURCE,DOC,INVENTORY,*PRIORS,*DEPENDENCIES,'scripts/compose_kinematic_replacement.py','scripts/check_kinematic_replacement.py','scripts/review_kinematic_replacement.py','tests/test_kinematic_replacement.py','scripts/check_rod_length_claims.py','scripts/check_rod_methods.py','scripts/check_coordinate_correspondence.py','scripts/check_material_relative_frame.py','scripts/check_tau_differential.py','scripts/compose_rod_methods.py','scripts/compose_material_body_motion.py','scripts/compose_material_relative_frame.py','scripts/compose_two_postulates.py','scripts/compose_relativity_conjecture.py','scripts/compose_limits.py'}
    return dict(status='tacit_kinematics_and_complete_geometric_replacement_connected_and_checked',document=FULL,**results,alignment=dict(segments=[dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),status='explicit_interpretive_annotation') for s in source['segments']]),verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,remaining=['u0034の全単位判断登録','u0035以降と二作品全体の目標'],source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
