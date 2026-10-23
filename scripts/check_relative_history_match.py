"""Check point identity, elapsed-time matching and opposite case roles."""
from fractions import Fraction as Q
from functools import lru_cache
from itertools import product
import json
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_coordinate_correspondence import abstract
from scripts.check_material_relative_frame import arithmetic,rotate,axes,BASE,LEFT,RIGHT,RS,FS,IDENTITY,NUM
from scripts.compose_relative_history_match import ROOT,read,PARENT,PARENT_BASIS,FULL,CORE,BASIS,ANNOTATIONS,FIELDS,CASE,COMMON,MEANINGS,build

DOC='docs/relative-history-match-v1.md';SOURCE='data/einstein-opening-obligations-v1.json'
PRIOR='data/einstein-author-credit-review-v1.json'
DOMAIN=('left','right',*LEFT,*RIGHT,'framea','frameb','length','timeunit','other')
SCENES=('first','second','other')


def record(p):return json.loads(read(p))
def forbidden(*a):raise ValueError('Unspecified history-comparison input')


@lru_cache(None)
def fixture(symbol):
    doc=parse(read(CORE));doc['statements']=[]
    abstract(doc,NUM|{'eiar'}|({'eia2','eiag','eiah'} if symbol=='eia3' else set()))
    d=next(d for d in doc['declarations'] if d['name']==symbol);slots=[];arguments=[]
    for i,p in enumerate(d['parameters']):
        n='jrhm'+number_word(i);slots.append((n,p['sort']))
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
        arguments.append(dict(kind='call',symbol=n,arguments=[]))
    doc['statements']=[dict(kind='ask',body=dict(kind='call',symbol=symbol,arguments=arguments))]
    return doc,slots


def run(symbol,values,model):
    doc,slots=fixture(symbol);assert len(slots)==len(values),(symbol,len(slots),len(values))
    model=dict(model)
    for (n,s),value in zip(slots,values,strict=True):
        if isinstance(s,dict) and not isinstance(value,FunctionValue):value=FunctionValue(tuple(s['parameters']),s['result'],value)
        model[n]=lambda value=value:value
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={n:model.get(n,forbidden) for n in names},max_steps=500000,
        memoize_definitions=False,memoize_expressions=False)[0]['value']


def setup(scenario='match',offset=Q(5)):
    offset=Q(offset);cuts,model=arithmetic();r=cuts.read
    upper2=offset+(4 if scenario=='time_dilated' else 2)
    def xyz(case,side,p,t):
        if scenario=='unknown_coordinate':raise ValueError('Unknown material coordinate')
        e=t-(offset if case=='second' else 0)
        name=({'q':'r','r':'q'}.get(p,p) if scenario=='point_swap' and case=='second' and side=='right' else p)
        values=tuple(map(Q,BASE.get(name,(9,8,7))))
        if case=='first':
            return (values[0]+e,values[1],values[2]) if side=='left' else values
        if side=='left' and scenario=='reference_rescaled':values=tuple(2*x for x in values)
        if side=='left' and scenario=='unmarked_shape' and p=='s':values=(values[0],values[1],values[2]+1)
        if side=='right':
            rate=Q(2) if scenario=='wrong_speed' else Q(-1) if scenario=='reversed' else Q(1,2) if scenario=='time_dilated' else Q(1)
            values=(values[0]-rate*e,values[1],values[2])
            if scenario=='endpoint_only':values=(values[0],values[1]+e*(2-e),values[2])
            if scenario=='wrong_y':values=(values[0],values[1]+1,values[2])
            if scenario=='wrong_z':values=(values[0],values[1],values[2]+1)
        if scenario=='global_rotation':values=rotate(values,Q(1))
        return tuple(x+y for x,y in zip(values,(10,20,30)))
    def basis(case,t):return axes(Q(1)) if case=='second' and scenario=='global_rotation' else IDENTITY
    def family(case,side,axis):
        return FunctionValue(('individual',),FS,lambda p:FunctionValue((RS,),RS,
            lambda t:cuts.make(xyz(case,side,p,r(t))[axis])))
    values=dict(left='left',right='right',lengthunit='length',timeunit='timeunit',
        leftmembers=lambda p:p in LEFT,rightmembers=lambda p:p in RIGHT,origin='o',guide='g',plane='h',offset=cuts.make(offset))
    for case in ('first','second'):
        values.update({case+'frame':'framea' if case=='first' else 'frameb',case+'context':case,
            case+'lower':cuts.make(0 if case=='first' else offset),case+'upper':cuts.make(2 if case=='first' else upper2)})
        for side in ('left','right'):
            for i,a in enumerate('xyz'):values[case+side+a]=family(case,side,i)
        for i,a in enumerate('uvw'):
            for j,b in enumerate('xyz'):
                values[case+a+b]=FunctionValue((RS,),RS,lambda t,case=case,i=i,j=j:cuts.make(basis(case,r(t))[i][j]))
    calls=[]
    def paired(*xs):
        case=xs[3]
        if scenario=='unknown_history':raise ValueError('Unknown complete pair history')
        calls.append(case)
        if case not in ('first','second') or scenario=='invalid_'+case:return False
        expected=('left','right','framea' if case=='first' else 'frameb',case,'length','timeunit',
            Q(0) if case=='first' else offset,Q(2) if case=='first' else upper2)
        if (*xs[:6],r(xs[6]),r(xs[7]))!=expected:return False
        if {p for p in DOMAIN if xs[8](p)}!=set(LEFT) or {p for p in DOMAIN if xs[9](p)}!=set(RIGHT):return False
        if xs[16:19]!=('o','g','h'):return False
        times=tuple((offset if case=='second' else 0)+Q(t) for t in (0,1,2))
        for i,fn in enumerate(xs[10:16]):
            side='left' if i<3 else 'right';population=LEFT if side=='left' else RIGHT
            if any(r(fn(p)(cuts.make(t)))!=xyz(case,side,p,t)[i%3] for p in population for t in times):return False
        return all(r(fn(cuts.make(t)))==basis(case,t)[i//3][i%3] for i,fn in enumerate(xs[19:]) for t in times)
    model['eiar']=paired
    return cuts,model,[values[n] for n,_ in FIELDS],values,xyz,basis,calls


@lru_cache(None)
def clock_checks():
    cuts,model=arithmetic();cases=[((0,2,5,7,5),True),((0,2,-3,-1,-3),True),((0,2,0,2,0),True),
        ((-2,1,4,7,6),True),((0,2,5,9,5),False),((0,2,5,7,-5),False),((0,2,7,5,5),False),
        ((0,0,5,5,5),False),((2,0,7,5,5),False),((0,2,6,7,5),False),((0,2,5,6,5),False)]
    for numbers,expected in cases:
        assert run('eiav',[cuts.make(n) for n in numbers],model)==expected,numbers
    values=[cuts.make(n) for n in (0,2,5,7,5)];model['ba']=lambda x:cuts.read(x)!=7
    assert run('eiav',values,model) is False
    return dict(cases=len(cases),negative_and_zero_offsets_allowed=True,empty_reversed_or_rescaled_intervals_rejected=True,
        invalid_endpoint_rejected=True,full_interval_correspondence_is_constant_translation=True)


@lru_cache(None)
def point_and_shape_checks():
    rows={};cases=0
    scenarios=('match','global_rotation','wrong_speed','reversed','endpoint_only','wrong_y','wrong_z',
        'point_swap','reference_rescaled','unmarked_shape','time_dilated','invalid_first','invalid_second')
    for scenario in scenarios:
        cuts,model,args,values,xyz,basis,calls=setup(scenario)
        prepared=run('eiax',args,model)
        assert prepared==(scenario not in ('time_dilated','invalid_first','invalid_second'))
        shape=run('eiay',args,model)
        assert shape==(prepared and scenario not in ('reference_rescaled','unmarked_shape')),(scenario,shape)
        answers=[]
        def local(case,p,t):
            delta=tuple(a-b for a,b in zip(xyz(case,'right',p,t),xyz(case,'left','o',t)))
            return tuple(sum(a*b for a,b in zip(delta,axis)) for axis in basis(case,t))
        for p in ('p','q','r','other'):
            for t in map(Q,(-1,0,1,2,3)):
                expected=(prepared and p in RIGHT and 0<=t<=2 and local('first',p,t)==local('second',p,t+5))
                actual=run('eiaz',args+[p,cuts.make(t)],model)
                assert actual==expected,(scenario,p,t,actual,expected);cases+=1;answers.append(actual)
        rows[scenario]=dict(prepared=prepared,reference_shape=shape,matching_point_times=sum(answers))
    for offset in (Q(-3),Q(0),Q(7,2)):
        cuts,model,args,*_=setup(offset=offset)
        assert run('eiay',args,model) is True
        assert run('eiaz',args+['q',cuts.make(1)],model) is True
    # Reverse the comparison and offset; the physical case identities remain.
    cuts,model,args,values,*_=setup()
    changed=dict(values)
    for n,_ in CASE:changed['first'+n],changed['second'+n]=values['second'+n],values['first'+n]
    changed['offset']=cuts.make(-5);reverse=[changed[n] for n,_ in FIELDS]
    assert run('eiay',reverse,model) is True and run('eiaz',reverse+['q',cuts.make(6)],model) is True
    for scenario in ('unknown_coordinate','unknown_history'):
        cuts,model,args,*_=setup(scenario)
        try:run('eiaz',args+['p',cuts.make(1)],model)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(scenario)
    return dict(cases=cases,scenarios=rows,comparison_direction_reversible=True,unknown_rejected=True,
        native_relative_projections_used=True,full_histories_are_boundary_inputs=True)


@lru_cache(None)
def binding_checks():
    cuts,model,args,values,*_=setup();r=cuts.read;mutations=[]
    for i,(n,sort) in enumerate(FIELDS):
        changed=list(args)
        if n in ('leftmembers','rightmembers'):changed[i]=lambda p:False
        elif n=='offset' or n.endswith(('lower','upper')):changed[i]=cuts.make(r(args[i])+1)
        elif sort=='a' or sort=='d':changed[i]='other'
        elif 'left' in n or 'right' in n:
            original=args[i]
            changed[i]=FunctionValue(original.parameters,original.result,
                lambda p,original=original:FunctionValue((RS,),RS,lambda t:cuts.make(r(original(p)(t))+1)))
        else:
            original=args[i];changed[i]=FunctionValue((RS,),RS,lambda t,original=original:cuts.make(r(original(t))+1))
        assert run('eiax',changed,model) is False,(i,n)
        mutations.append(n)
    return dict(all_prepared_comparison_arguments_mutated=len(mutations),rejected_argument_names=mutations,
        shared_object_point_unit_and_marker_scope_preserved=True)


@lru_cache(None)
def role_and_domain_checks():
    cuts,model,args,values,*_=setup();r=cuts.read;count=0
    expected=[('eiag','left','framea','first'),('eiah','right','framea','first'),
        ('eiah','left','frameb','second'),('eiag','right','frameb','second')]
    for bits in product((False,True),repeat=5):
        calls=[];local=dict(model,eia2=lambda *a:bits[0])
        def condition(name):
            def evaluate(*xs):
                key=(name,*xs[:3]);calls.append(key)
                if key not in expected:return False
                i=expected.index(key);case=xs[2];side=xs[0]
                assert xs[3:5]==('length','timeunit')
                assert (r(xs[5]),r(xs[6]))==((0,2) if case=='first' else (5,7))
                assert {p for p in DOMAIN if xs[7](p)}==set(LEFT if side=='left' else RIGHT)
                for axis,fn in zip('xyz',xs[8:]):
                    original=values[case+side+axis]
                    for point in (LEFT if side=='left' else RIGHT):
                        for t in ((0,1,2) if case=='first' else (5,6,7)):
                            assert r(fn(point)(cuts.make(t)))==r(original(point)(cuts.make(t)))
                return bits[i+1]
            return evaluate
        local.update(eiag=condition('eiag'),eiah=condition('eiah'))
        assert run('eia3',args,local)==all(bits);assert calls==expected;count+=1
    try:run('eia2',args,model)
    except ValueError as error:assert 'rational number domain' in str(error)
    else:raise AssertionError('Full continuous history silently sampled')
    return dict(five_condition_combinations=count,motion_and_rest_cases=expected,
        each_role_uses_exact_body_frame_context_units_interval_population_and_curves=True,
        real_domain_refused='eia2',full_motion_definitions_boundary_only=True)


@lru_cache(None)
def structure_checks():
    for p,b in build().items():assert read(p)==b,p
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==207
    assert new.document['declarations'][:len(old.document['declarations'])]==old.document['declarations']
    assert all(new.entries[n]['meaning_ja']==e['meaning_ja'] for n,e in old.entries.items())
    prior=record(PRIOR);validate_hashes(ROOT,prior['source_sha256']);assert selection_binding(new,[206])==prior['selection']
    load_annotations(ROOT,BASIS,ANNOTATIONS);doc=parse(read(CORE))
    for style in ('compact','full'):
        text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    return dict(new_definitions=7,new_primitives=0,preserved_statements=207,author_review_preserved=True,
        core_roundtrips=['compact','full','v2'])


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={n:fn() for n,fn in [('clock',clock_checks),('points_and_shape',point_and_shape_checks),
        ('bindings',binding_checks),('roles_and_domains',role_and_domain_checks),('structure',structure_checks)]}
    paths=set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{DOC,SOURCE,PRIOR,
        'scripts/compose_relative_history_match.py','scripts/check_relative_history_match.py',
        'scripts/compose_material_relative_frame.py','scripts/compose_limits.py',
        'scripts/check_material_relative_frame.py','scripts/check_tau_differential.py',
        'scripts/check_coordinate_correspondence.py','tests/test_relative_history_match.py'}
    return dict(status='relative_history_match_dependency_checked',document=FULL,**results,
        full_real_domain_evaluated=False,source_text_coverage_added=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
