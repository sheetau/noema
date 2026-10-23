"""Check body-point scope, interval witnesses and native coordinate incidence."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse, format_graph, number_word
from noema.finite_semantics import FunctionValue, evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_tau_differential import ConstructedCuts
from scripts.compose_material_body_motion import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,MEANINGS,build,read

DOC='docs/material-body-motion-v1.md'
SOURCE='data/einstein-opening-obligations-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json'
DOMAIN=('body','p','q','other','frame','length','timeunit','event')
SCENES=('context','other')


def record(path):return json.loads(read(path))
def forbidden(*args):raise ValueError('Unspecified material-body input')


@lru_cache(None)
def fixture(symbol, trajectory_boundary=True, path=CORE):
    doc=parse(read(path));doc['statements']=[]
    # No finite domain is substituted for the continuum: only these named
    # old operations are boundaries. zzbg/lg/sb and every new body stay native.
    abstract(doc,{'zzba','zzbc'}|({'se'} if trajectory_boundary else set()))
    d=next(d for d in doc['declarations'] if d['name']==symbol)
    arguments=[];slots=[]
    for i,p in enumerate(d['parameters']):
        name='jmb'+number_word(i)
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=p['sort']))
        slots.append((name,p['sort']));arguments.append(dict(kind='call',symbol=name,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots


def run(symbol,values,model,trajectory_boundary=True,path=CORE):
    doc,slots=fixture(symbol,trajectory_boundary,path)
    assert len(values)==len(slots)
    model=dict(model)
    for (name,sort),value in zip(slots,values,strict=True):
        if isinstance(sort,dict) and not isinstance(value,FunctionValue):
            value=FunctionValue(tuple(sort['parameters']),sort['result'],value)
        model[name]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    supplied={n:model.get(n,forbidden) for n in names}
    return evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=supplied,
        max_steps=100000,memoize_definitions=False,memoize_expressions=False)[0]['value']


def position(profile,point,t):
    sign=1 if point=='p' else -1
    base=(Fraction(sign),Fraction(0),Fraction(0))
    if profile in ('x','y','z'):
        return tuple(x+(t if i=='xyz'.index(profile) else 0) for i,x in enumerate(base))
    if profile=='return':return (base[0]+(t if t<=1 else 2-t),base[1],base[2])
    if profile=='rotation':
        s=t if t<=1 else 2-t
        return (sign*((s*s-1) if t<=1 else (1-s*s))/(1+s*s),sign*2*s/(1+s*s),Fraction(0))
    if profile=='one_point':return (base[0]+(t if point=='q' else 0),base[1],base[2])
    return base


def setup(profile='x',variant=None):
    cuts=ConstructedCuts();r=cuts.read
    declared={'p','q'};actual={'p','q'}
    if variant=='empty':declared=set();actual=set()
    if variant=='omitted_point':declared={'p'}
    if variant=='extra_point':declared.add('other')
    if variant=='different_body_parts':actual={'other'}
    def parts(body,point,context):
        if variant=='unknown_parts':raise ValueError('Unknown material points')
        return (body,context)==('body','context') and point in actual
    model={'zm':lambda b:b=='body' and variant!='not_body','eirh':parts,
        'zzba':lambda c:isinstance(r(c),Fraction), 'zzbc':lambda a,b:r(a)<=r(b)}
    rs=dict(kind='function',parameters=['number'],result='truth')
    fs=dict(kind='function',parameters=[rs],result=rs)
    def family(axis):
        def select(point):
            def at(time):
                if variant=='unknown_position':raise ValueError('Unknown spatial value')
                return cuts.make(position(profile,point,r(time))[axis])
            return FunctionValue((rs,),rs,at)
        return FunctionValue(('individual',),fs,select)
    families=[family(i) for i in range(3)]
    def trajectory(point,frame,context,length,timeunit,lower,upper,*curves):
        if variant=='unknown_trajectory':raise ValueError('Unknown complete trajectory')
        if variant=='missing_point_trajectory' and point=='q':return False
        expected=('frame','context','length','timeunit',Fraction(0),Fraction(2))
        received=(frame,context,length,timeunit,r(lower),r(upper))
        return point in actual and received==expected and all(
            tuple(r(fn(cuts.make(t))) for t in (0,1,2))==tuple(position(profile,point,Fraction(t))[i] for t in (0,1,2))
            for i,fn in enumerate(curves)) and variant!='invalid_history'
    model['se']=trajectory
    values=['body','frame','context','length','timeunit',cuts.make(0),cuts.make(2),lambda p:p in declared,*families]
    return cuts,model,values,families


@lru_cache(None)
def scope_checks():
    results={}
    for variant in (None,'empty','omitted_point','extra_point','different_body_parts','not_body',
                    'missing_point_trajectory','invalid_history'):
        cuts,model,args,_=setup(variant=variant)
        answer=run('eiad',args,model);assert answer==(variant is None),(variant,answer)
        results[variant or 'baseline']=answer
    cuts,model,args,_=setup()
    changed=list(args);changed[4]=changed[3]
    assert run('eiad',changed,model) is False
    for variant in ('unknown_parts','unknown_trajectory'):
        cuts,model,args,_=setup(variant=variant)
        try:run('eiad',args,model)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    return dict(complete_population_and_history=results,same_length_time_unit_rejected=True,unknown_rejected=True)


@lru_cache(None)
def witness_checks():
    rows={};cases=0
    for profile in ('rest','x','y','z','return','rotation','one_point'):
        cuts,model,args,families=setup(profile)
        outcomes=[]
        for point in ('p','q','other'):
            for first,second in ((0,1),(0,2),(1,2),(2,0),(1,1),(-1,1),(1,3)):
                expected=(point in ('p','q') and 0<=first<second<=2 and
                    position(profile,point,Fraction(first))!=position(profile,point,Fraction(second)))
                actual=run('eiaf',args+[point,cuts.make(first),cuts.make(second)],model)
                assert actual==expected,(profile,point,first,second,actual,expected)
                outcomes.append(actual);cases+=1
        rows[profile]=sum(outcomes)
    # The same occupied endpoint set is compatible with changed material points.
    assert {position('rotation',p,Fraction(0)) for p in ('p','q')}=={position('rotation',p,Fraction(2)) for p in ('p','q')}
    for flag in ('invalid_history','omitted_point','missing_point_trajectory'):
        cuts,model,args,_=setup(variant=flag)
        assert run('eiaf',args+['p',cuts.make(0),cuts.make(1)],model) is False
    cuts,model,args,_=setup(variant='unknown_position')
    try:run('eiaf',args+['p',cuts.make(0),cuts.make(1)],model)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown coordinate was completed')
    return dict(cases=cases,accepted_witnesses=rows,return_between_endpoints_retained=True,
        occupied_set_does_not_replace_material_identity=True,invalid_history_not_motion=True)


@lru_cache(None)
def coordinate_checks():
    cases=0
    for changed in (None,*range(13)):
        cuts,model,args,families=setup('x');r=cuts.read
        def incidence(point,event,context):
            expected=['p','event','context']
            if changed in (0,1,2):expected[changed]='other'
            return (point,event,context)==tuple(expected)
        def coordinate(event,frame,context,length,timeunit,*coords):
            expected=['event','frame','context','length','timeunit',Fraction(1),Fraction(2),Fraction(0),Fraction(0)]
            if changed is not None and 3<=changed<=11:
                slot=changed-3;expected[slot]='other' if slot<5 else Fraction(99)
            return (event,frame,context,length,timeunit,*(r(c) for c in coords))==tuple(expected)
        model.update(zzbv=incidence,zzbu=coordinate)
        if changed==12:model['eirh']=lambda *a:False
        values=['body','p','event','frame','context','length','timeunit',cuts.make(1),*families]
        actual=run('eiai',values,model)
        assert actual==(changed is None),(changed,actual);cases+=1
    return dict(native_sb_and_sa=True,material_event_frame_context_units_and_all_coordinates=cases,
        whole_interval_not_inferred=True)


@lru_cache(None)
def binding_and_domain_checks():
    # Distinguishable inputs at every se parameter, including each coordinate
    # family, rather than a truth-only stub that could conceal argument swaps.
    cuts,model,args,families=setup('rotation');seen=[]
    original=model['se']
    def spy(*values):seen.append(values);return original(*values)
    model['se']=spy
    assert run('eiad',args,model) is True
    # Implication evaluates its operands eagerly in this finite evaluator.
    assert [v[0] for v in seen]==list(DOMAIN)
    assert [v[0] for v in seen if v[0] in ('p','q')]==['p','q']
    changes={0:'other',1:'other',2:'other',3:'other',4:'other',
        5:cuts.make(Fraction(1,2)),6:cuts.make(3),7:lambda p:p=='p',
        8:families[1],9:families[0],10:families[0]}
    for slot,value in changes.items():
        changed=list(args);changed[slot]=value
        assert run('eiad',changed,model) is False,slot
    # Selecting the other material point's path must fail even when the same
    # set of spatial endpoints is occupied by the two points.
    shifted=[]
    for family in families:
        shifted.append(FunctionValue(family.parameters,family.result,
            lambda point,family=family:family('q' if point=='p' else 'p')))
    assert run('eiad',args[:8]+shifted,model) is False
    for symbol in ('eiag','eiah'):
        try:run(symbol,args,model)
        except ValueError as error:assert 'rational number domain' in str(error)
        else:raise AssertionError('Full real domain silently sampled: '+symbol)
    try:run('eiad',args,model,trajectory_boundary=False)
    except ValueError as error:assert 'rational number domain' in str(error)
    else:raise AssertionError('Native se continuum silently sampled')
    return dict(all_material_points_share_ten_trajectory_arguments=True,
        changed_history_argument_slots_rejected=list(changes),swapped_material_point_paths_rejected=True,
        full_domain_refused=['eiag','eiah','eiad_with_native_se'], finite_time_quantification_substituted=False)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]['meaning_ja']==e['meaning_ja']
    prior=record(PRIOR);validate_hashes(ROOT,prior['source_sha256'])
    assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE))
    for notation in ('compact','full'):
        text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(preserved_statements=207,preserved_author_review=True,new_definitions=7,new_primitives=1,
        no_new_author_assertion=True,core_roundtrips=['compact','full','v2'])


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={name:fn() for name,fn in [('scope',scope_checks),('witnesses',witness_checks),
        ('coordinates',coordinate_checks),('binding_and_domains',binding_and_domain_checks),('structure',structure_checks)]}
    pins=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_material_body_motion.py','scripts/check_material_body_motion.py','tests/test_material_body_motion.py',
        'scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','scripts/compose_limits.py'}
    return dict(status='material_body_motion_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(pins)})
