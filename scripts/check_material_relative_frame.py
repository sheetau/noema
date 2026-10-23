"""Check anchored orientation, projections and relative-motion witnesses."""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from itertools import permutations,product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_tau_differential import ConstructedCuts
from scripts.compose_material_relative_frame import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,MEANINGS,build

DOC='docs/material-relative-frame-v1.md'
SOURCE='data/einstein-opening-obligations-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json'
NUM={'ba','bb','bc','bd','bf','shv','sca','zzba','zzbc'}
DOMAIN=('left','right','o','g','h','s','p','q','r','frame','length','timeunit','other')
LEFT=('o','g','h','s');RIGHT=('p','q','r')
RS=dict(kind='function',parameters=['number'],result='truth')
FS=dict(kind='function',parameters=[RS],result=RS)
IDENTITY=((Q(1),Q(0),Q(0)),(Q(0),Q(1),Q(0)),(Q(0),Q(0),Q(1)))


def record(p):return json.loads(read(p))
def forbidden(*args):raise ValueError('Unspecified relative-frame input')
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def rotate(point,t):
    c=(1-t*t)/(1+t*t);s=2*t/(1+t*t)
    return (c*point[0]-s*point[1],s*point[0]+c*point[1],point[2])
def axes(t):return tuple(rotate(p,t) for p in IDENTITY)


@lru_cache(None)
def fixture(symbol,native_reference=False):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|{'eiad'}|(set() if native_reference else {'eiaq'}))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jmrf'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    expression=dict(kind='call',symbol=symbol,arguments=arguments)
    if d['result']!='truth':
        doc['declarations'].append(dict(kind='primitive',name='jmrcapture',parameters=[d['result']],result='truth'))
        expression=dict(kind='call',symbol='jmrcapture',arguments=[expression])
    doc['statements']=[dict(kind='ask',body=expression)]
    return doc,slots


def run(symbol,values,model,native_reference=False):
    doc,slots=fixture(symbol,native_reference);assert len(values)==len(slots)
    model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    captured=[]
    def capture(value):captured.append(value);return True
    model['jmrcapture']=capture
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    result=evaluate_document(doc,individuals=DOMAIN,situations=('context','other'),
        primitives={n:model.get(n,forbidden) for n in names},max_steps=300000,
        memoize_definitions=False,memoize_expressions=False)
    return captured[0] if captured else result[0]['value']


def arithmetic():
    cuts=ConstructedCuts();r=cuts.read;c=cuts.make
    model=dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),
        bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),
        shv=lambda a,b:c(r(a)*r(b)),sca=lambda a,b:r(a)==r(b),
        zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b))
    return cuts,model


BASE={'o':(0,0,0),'g':(2,0,0),'h':(1,3,0),'s':(0,0,4),'p':(4,0,0),'q':(4,1,0),'r':(4,0,1)}


def setup(scenario='static',variant=None):
    cuts,model=arithmetic();r=cuts.read
    def xyz(side,point,t):
        if variant=='unknown_coordinate':raise ValueError('Unknown point coordinate')
        p=tuple(map(Q,BASE.get(point,(7,8,9))))
        if side=='left':
            if point=='g' and variant=='zero_guide':p=(Q(0),Q(0),Q(0))
            if point=='h' and variant=='collinear':p=(Q(3),Q(0),Q(0))
            if point=='h' and variant=='wrong_plane':p=(Q(1),Q(3),Q(1))
            if point=='h' and variant=='opposite_plane':p=(Q(1),Q(-3),Q(0))
            if point=='s' and scenario=='deformed_reference':p=(Q(0),Q(0),4+t)
        if scenario in ('common_rotation','reference_rotation') and (scenario=='common_rotation' or side=='left'):
            p=rotate(p,t)
        if scenario=='right_rotation' and side=='right':
            p=tuple(x+y for x,y in zip(rotate(minus(p,(4,0,0)),t),(4,0,0)))
        if scenario=='common_translation':p=tuple(x+y*t for x,y in zip(p,(1,-2,3)))
        if scenario in ('relative_translation','return') and side=='right':
            shift=t if scenario=='relative_translation' or t<=1 else 2-t
            p=(p[0]+shift,p[1],p[2])
        return p
    def basis(t):
        return axes(t) if scenario in ('common_rotation','reference_rotation') else IDENTITY
    def family(side,axis):
        return FunctionValue(('individual',),FS,
            lambda point:FunctionValue((RS,),RS,lambda time:cuts.make(xyz(side,point,r(time))[axis])))
    left=[family('left',i) for i in range(3)];right=[family('right',i) for i in range(3)]
    frame=[FunctionValue((RS,),RS,lambda time,i=i,j=j:cuts.make(basis(r(time))[i][j])) for i in range(3) for j in range(3)]
    def parts(body,point,context):
        if variant=='unknown_parts':raise ValueError('Unknown material membership')
        return context=='context' and point in (LEFT if body=='left' else RIGHT if body=='right' else ())
    model.update(zm=lambda b:b in ('left','right'),eirh=parts)
    def history(side,values):
        body,chart,context,length,timeunit,lower,upper,members,*families=values
        if (body,chart,context,length,timeunit,r(lower),r(upper))!=(side,'frame','context','length','timeunit',Q(0),Q(2)):return False
        population=LEFT if side=='left' else RIGHT
        if {p for p in DOMAIN if members(p)}!=set(population):return False
        return all(tuple(r(fn(p)(cuts.make(t))) for t in (0,1,2))==tuple(xyz(side,p,Q(t))[i] for t in (0,1,2))
            for i,fn in enumerate(families) for p in population)
    def reference(*values):
        if variant=='unknown_reference':raise ValueError('Unknown rigid reference history')
        if variant=='invalid_reference' or scenario=='deformed_reference':return False
        return (history('left',values[:11]) and values[11:14]==('o','g','h') and all(
            tuple(r(fn(cuts.make(t))) for t in (0,1,2))==tuple(basis(Q(t))[i//3][i%3] for t in (0,1,2))
            for i,fn in enumerate(values[14:])))
    def target(*values):
        if variant=='unknown_target':raise ValueError('Unknown complete target history')
        return variant!='invalid_target' and history('right' if values[0]=='right' else 'left',values)
    model.update(eiaq=reference,eiad=target)
    pair=['left','right','frame','context','length','timeunit',cuts.make(0),cuts.make(2),
        lambda p:p in LEFT,lambda p:p in RIGHT,*left,*right,'o','g','h',*frame]
    instant=['left','context',pair[8],*left,'o','g','h',cuts.make(0),*frame]
    project=['o',*left,*right,*frame]
    return cuts,model,pair,instant,project,xyz,basis


@lru_cache(None)
def orientation_checks():
    cuts,model=arithmetic();accepted=0;rejected=0
    for perm in permutations(range(3)):
        for signs in product((-1,1),repeat=3):
            basis=tuple(tuple(Q(signs[i])*IDENTITY[perm[i]][j] for j in range(3)) for i in range(3))
            expected=dot(cross(basis[0],basis[1]),basis[2])==1
            actual=run('eiaj',[cuts.make(x) for row in basis for x in row],model)
            assert actual==expected,(basis,actual)
            accepted+=actual;rejected+=not actual
    for slot in range(9):
        values=[cuts.make(x) for row in IDENTITY for x in row]
        values[slot]=cuts.make(Q(slot//3==slot%3)+1)
        assert run('eiaj',values,model) is False
    for variant in (None,'zero_guide','collinear','wrong_plane','opposite_plane'):
        cuts,model,pair,instant,*_=setup(variant=variant)
        assert run('eial',instant,model)==(variant is None),variant
    cuts,model,pair,instant,*_=setup()
    for slot in (0,1,6,7,8):
        changed=list(instant);changed[slot]='other'
        assert run('eial',changed,model) is False,slot
    changed=list(instant);changed[7]=changed[6]
    assert run('eial',changed,model) is False
    for variant in ('unknown_parts','unknown_coordinate'):
        cuts,model,pair,instant,*_=setup(variant=variant)
        try:run('eial',instant,model)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    return dict(proper_signed_axis_frames=accepted,reflected_frames_rejected=rejected,
        nine_component_mutations_rejected=True,nonorthogonal_marker_displacement_allowed=True,
        degenerate_or_unanchored_frames_rejected=True,unknown_rejected=True)


@lru_cache(None)
def projection_checks():
    count=0
    for scenario in ('static','relative_translation','common_translation','common_rotation','reference_rotation','right_rotation','return'):
        cuts,model,pair,instant,project,xyz,basis=setup(scenario)
        functions=[run(n,project,model) for n in ('eian','eiao','eiap')]
        for point in RIGHT:
            for t in map(Q,(0,1,2)):
                expected=tuple(dot(minus(xyz('right',point,t),xyz('left','o',t)),axis) for axis in basis(t))
                actual=tuple(cuts.read(fn(point)(cuts.make(t))) for fn in functions)
                assert actual==expected,(scenario,point,t,actual,expected);count+=1
                if scenario in ('static','common_translation','common_rotation'):
                    assert actual==BASE[point]
        if scenario=='reference_rotation':
            before=tuple(cuts.read(fn('p')(cuts.make(0))) for fn in functions)
            after=tuple(cuts.read(fn('p')(cuts.make(1))) for fn in functions)
            assert before!=after and dot(before,before)==dot(after,after)
    return dict(exact_projection_cases=count,common_rigid_motion_cancelled_in_relative_configuration=True,
        fixed_distance_not_relative_rest=True,physics_invariance_not_claimed=True)


@lru_cache(None)
def witness_checks():
    count=0;totals={}
    for scenario in ('static','relative_translation','common_translation','common_rotation','reference_rotation','right_rotation','return'):
        cuts,model,pair,instant,project,xyz,basis=setup(scenario);accepted=0
        local=lambda p,t:tuple(dot(minus(xyz('right',p,Q(t)),xyz('left','o',Q(t))),axis) for axis in basis(Q(t)))
        for point in ('p','q','other'):
            for first,second in ((0,1),(0,2),(1,2),(2,0),(1,1),(-1,1),(1,3)):
                expected=point in RIGHT and 0<=first<second<=2 and local(point,first)!=local(point,second)
                actual=run('eias',pair+[point,cuts.make(first),cuts.make(second)],model)
                assert actual==expected,(scenario,point,first,second,actual,expected)
                accepted+=actual;count+=1
        totals[scenario]=accepted
    for variant in ('invalid_reference','invalid_target'):
        cuts,model,pair,*_=setup('relative_translation',variant)
        assert run('eias',pair+['p',cuts.make(0),cuts.make(1)],model) is False
    return dict(cases=count,accepted_witnesses=totals,invalid_histories_not_relative_motion=True)


@lru_cache(None)
def binding_and_domain_checks():
    cuts,model,pair,instant,project,xyz,basis=setup('common_rotation')
    assert run('eiar',pair,model) is True
    changed_slots=[]
    for slot in range(len(pair)):
        changed=list(pair)
        if slot in (6,7):changed[slot]=cuts.make(-1 if slot==6 else 3)
        elif slot in (8,9):changed[slot]=lambda p:False
        elif 10<=slot<=15:
            original=pair[slot]
            changed[slot]=FunctionValue(original.parameters,original.result,
                lambda point,original=original:FunctionValue((RS,),RS,
                    lambda t:cuts.make(cuts.read(original(point)(t))+1)))
        elif slot>=19:
            original=pair[slot]
            changed[slot]=FunctionValue((RS,),RS,lambda t,original=original:cuts.make(cuts.read(original(t))+1))
        else:changed[slot]='other'
        assert run('eiar',changed,model) is False,slot
        changed_slots.append(slot)
    for variant in ('unknown_reference','unknown_target'):
        cuts,model,pair,*_=setup(variant=variant)
        try:run('eiar',pair,model)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    # A non-marker material point deforms although all three frame anchors
    # remain valid. Its native projected-coordinate difference witnesses the
    # failure of eiaq's universal rigidity clause, without sampling that clause.
    cuts,model,pair,instant,project,*_=setup('deformed_reference')
    assert run('eial',instant,model) is True
    self_project=['o',*pair[10:13],*pair[10:13],*pair[19:]]
    functions=[run(n,self_project,model) for n in ('eian','eiao','eiap')]
    assert run('eiae',['s',cuts.make(0),cuts.make(1),*functions],model) is True
    for point in ('o','g','h'):
        assert run('eiae',[point,cuts.make(0),cuts.make(1),*functions],model) is False
    cuts,model,pair,*_=setup()
    for symbol in ('eiat','eiau'):
        try:run(symbol,pair,model)
        except ValueError as error:assert 'rational number domain' in str(error)
        else:raise AssertionError('Real time domain sampled: '+symbol)
    history=[pair[0],*pair[2:8],pair[8],*pair[10:13],*pair[16:]]
    try:run('eiaq',history,model,native_reference=True)
    except ValueError as error:assert 'rational number domain' in str(error)
    else:raise AssertionError('Reference continuum silently sampled')
    return dict(paired_history_argument_mutations_rejected=changed_slots,
        unmarked_deformation_counterexample=True,unknown_histories_rejected=True,
        real_domain_refused=['eiaq','eiat','eiau'],physical_full_history_given_as_boundary=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=record(PRIOR);validate_hashes(ROOT,prior['source_sha256'])
    assert selection_binding(new,[206])==prior['selection'];load_annotations(ROOT,BASIS,ANNOTATIONS)
    doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=len(MEANINGS),new_primitives=0,preserved_statements=207,
        author_review_preserved=True,core_roundtrips=['compact','full','v2'])


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={n:fn() for n,fn in [('orientation',orientation_checks),('projection',projection_checks),
        ('witnesses',witness_checks),('bindings_and_domains',binding_and_domain_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_material_relative_frame.py','scripts/check_material_relative_frame.py',
        'scripts/compose_material_body_motion.py','scripts/compose_limits.py',
        'scripts/check_tau_differential.py','scripts/check_coordinate_correspondence.py','tests/test_material_relative_frame.py'}
    return dict(status='material_reference_frame_relative_motion_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
