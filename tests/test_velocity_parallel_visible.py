"""Distinguishing diagnostics for decoded third-frame, derivation and group definitions.

All selected definitions come from the recovered Native document. Finite
arithmetic models, abstraction boundaries and exposed binders are diagnostics,
not a proof over all real cuts or an independent reading of the source.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json,re
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,QuestionValue,evaluate_document
from scripts import check_einstein_velocity_parallel_visible as check
from scripts import velocity_axial_visible_profile as profile
from itertools import product
from scripts.check_translated_light_trial import expose
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (velocity-parallel-visible fixture)')

def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    if isinstance(x,SequenceValue):return tuple(value(v) for v in x.items)
    return x

def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows

def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            test(model|{name:forbidden})

def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows)
    return count

class Cuts:
    def __init__(self):self.table={}
    def make(self,n):
        n=Q(n);f=FunctionValue(('number',),'truth',lambda q:q<n)
        self.table[f.implementation]=n;return f
    def read(self,f):
        while isinstance(f,FunctionValue):
            impl=f.implementation
            if impl in self.table:return self.table[impl]
            if isinstance(impl,FunctionValue):f=impl;continue
            code=getattr(impl,'__code__',None)
            if code is None:break
            free=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(impl,'__closure__',None) or ()))))
            f=free.get('raw')
        raise ValueError('Unregistered finite cut')

def numbers():
    cuts=Cuts();c=cuts.make;r=cuts.read
    return cuts,dict(ba=lambda x:isinstance(r(x),Q),bb=c,bc=lambda a,b:r(a)<=r(b),
        bd=lambda a,b:c(r(a)+r(b)),bf=lambda a,b:c(r(a)-r(b)),
        bg=lambda a,b:r(a)<r(b),shv=lambda a,b:c(r(a)*r(b)),sah=lambda a,b:c(r(a)*r(b)),
        sca=lambda a,b:r(a)==r(b),zzba=lambda x:isinstance(r(x),Q),zzbc=lambda a,b:r(a)<=r(b),zzbg=lambda a,b:r(a)<r(b))




from scripts import check_parallel_current_records as current
from scripts import check_parallel_alternative_claim as alternative
from scripts import check_parallel_group_claim as group_claim
from scripts import check_velocity_composition_claim as composition
from scripts import check_moving_trip_geometry as trip

MODULES=dict(current=current,alternative=alternative,group=group_claim)
CHECKS=dict(current=('numeric_checks','record_checks','geometry_checks','scope_checks'),
    alternative=('numeric_checks','origin_checks','bridge_checks','method_checks','presentation_checks'),
    group=('necessity_checks','group_checks','presentation_checks'))


@lru_cache(None)
def native_blueprint(serialized):
    old=json.loads(serialized);doc=normalize_document(renamed(old,mapping()))
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    for i,(original,d) in enumerate(zip(old['declarations'],doc['declarations'],strict=True)):
        if d['kind']!='definition':continue
        # Finite selector installed by the method diagnostic is a model boundary.
        if original['name']=='zlx':
            assert recovered[d['name']]['kind']=='primitive'
            continue
        assert d['name'] in recovered,original['name']
        actual=deepcopy(recovered[d['name']])
        assert actual==d,('Source/Native definition differs',original['name'])
        doc['declarations'][i]=actual
    return normalize_document(doc)


def native_evaluate(document,*,primitives,**options):
    doc=native_blueprint(json.dumps(document,sort_keys=True))
    handlers={mapping().get(name,name):fn for name,fn in primitives.items()}
    # The historical attribution fixture compares quoted source identifiers
    # directly, unlike its other callbacks which use value(). Translate only
    # this diagnostic boundary; keep the evaluated Native and quotes intact.
    inverse={v:k for k,v in mapping().items()}
    def source_quote(x):
        if not isinstance(x,DescriptionValue):return x
        return DescriptionValue(check.canonical(renamed(json.loads(x.syntax),inverse)),x.result_type,x.rank)
    for name in ('ug','zc'):
        if name in primitives:
            fn=primitives[name]
            handlers[mapping().get(name,name)]=lambda *xs,fn=fn:fn(*(source_quote(x) for x in xs))
    return evaluate_document(doc,primitives=handlers,**options)


def run(group,name,args,m,*pos,**options):
    source=MODULES[group]
    mode=options.pop('mode','boundary');program=options.pop('program','')
    domain=options.pop('domain',source.DOMAIN);assert not options
    if pos:
        assert len(pos)==1
        if group=='alternative':program=pos[0]
        elif group=='group':mode=pos[0]
        else:domain=pos[0]
    blueprint,slots=source.fixture(name,program if group=='alternative' else mode)
    assert len(args)==len(slots)
    prefix={'current':'jpcr','alternative':'jpac','group':'jpgc'}[group]
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{prefix+'point':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args,strict=True)}
    return native_evaluate(blueprint,individuals=domain,situations=source.POINTS,
        primitives={d['name']:mm.get(d['name'],forbidden) for d in blueprint['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value,value=value,SemanticError=ValueError,evaluate_document=native_evaluate)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    arithmetic=clone(composition,('arithmetic',))['arithmetic']
    norm=clone(trip,('norm_factory',))['norm_factory']
    return {group:clone(module,CHECKS[group],dict(arithmetic=arithmetic,norm_factory=norm,
        run=lambda *a,g=group,**kw:run(g,*a,**kw))) for group,module in MODULES.items()}


@pytest.mark.parametrize('group,name',[(g,n) for g in MODULES for n in CHECKS[g]])
def test_decoded_parallel_distinguishing_models(group,name):assert models()[group][name]()


def test_whole_source_parent_and_designation():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(14,19))
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(147,150)]
    parent=check.previous.document();assert len(doc['statements'])==187 and doc['statements'][:181]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==861 and len(check.NEW_DEFINITIONS)==56
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(0,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(5,154,33)
    old={d['name']:d for d in check.source_excerpt()['declarations']}
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)
    assert len(b['annotations']['entries'])==1 and check.FORMS=={'eispa':'k′'}
    assert doc['statements'][-1]['body']['symbol']==check.vocabulary()._symbols['printedform']


def reference_values():
    cuts,_=numbers();b=dict(check.BASE);b['zlt']=cuts.make(-3)
    return b,cuts


def test_reference_positions_types_and_unknown_arguments():
    b,_=reference_values();h=check.context_handlers(b);cases=[]
    for old,pos in check.SENTENCES.items():cases.append(('sentencereference',[b['ri'],*map(Q,pos)],b[old]))
    for old,(node,start,end) in check.SPANS.items():cases.append(('sentencetokenspanreference',[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']],b[old]))
    for old,(node,index) in check.DESIGNATIONS.items():cases.append(('designationreference',[b['eirf'],b[node],Q(index),b['ri']],b[old]))
    for old in check.ROLE_ASSIGNMENTS:
        kind=check.reference_kind(old);sort=check.REFERENCE_SORTS[old]
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
            check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        cases.append((kind,args,b[old]))
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[kind](*args[:2],bad,args[3])
    for kind,args,expected in cases:
        assert h[kind](*args)==expected
        for slot in range(len(args)):
            bad=args[:];bad[slot]=Q(999) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[kind](*bad)
    assert len({b[n] for n in ('zlr','zls','zlu','zm3')})==4
    assert [len(r['tokens']) for r in check.text_boundaries()['sentences'].values()]==[26,83]


def test_native_reference_lookup_does_not_evaluate_role_or_claim():
    b,cuts=reference_values()
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS):
        doc=deepcopy(check.restored()['document']);sort=check.REFERENCE_SORTS.get(old,'individual')
        doc['declarations'].append(dict(kind='primitive',name='parallelcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('parallelcapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['parallelcapture']=(lambda x:cuts.read(x)==cuts.read(b[old])) if sort==RS else lambda x:x==b[old]
        declared={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        assert evaluate_document(doc,individuals=tuple({x for x in b.values() if isinstance(x,str)}|{'other'}),
            situations=check.SITUATIONS,primitives={n:handlers[n] for n in declared})[0]['value']


@lru_cache(None)
def role_fixture(old):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=deepcopy(ds[check.reference_roles()[old]]);decls=[]
    for name in sorted(_references(role['body'])):
        d=ds[name];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=name,parameters=parameters,result=d['result']))
    decls.extend([dict(kind='primitive',name='parallelcandidate',parameters=[],result=check.REFERENCE_SORTS[old]),
                  dict(kind='primitive',name='parallelcontext',parameters=[],result='situation')])
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[role],
        statements=[dict(kind='ask',body=call(role['name'],call('parallelcandidate'),call('parallelcontext')))]))


def run_role(old,candidate,model,context='reference'):
    doc=role_fixture(old);handlers={mapping().get(n,n):fn for n,fn in model.items()}
    handlers.update(parallelcandidate=lambda:candidate,parallelcontext=lambda:context)
    return evaluate_document(doc,individuals=('K','k','third','other','intro','paper','method'),
        situations=('reference','context','earlier','other'),
        primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'})[0]['value']


def test_third_frame_role_binds_introduction_and_excludes_existing_frames():
    rows={'va':{('third',)},'eisd3':{('intro','third','paper','reference')}}
    model={n:relation(rs) for n,rs in rows.items()}|{n:lambda x=x:x for n,x in {'ra':'K','zbm':'k','zlr':'intro','eirf':'paper'}.items()}
    assert perturb(lambda m:run_role('zlo','third',m),model,rows)
    assert not run_role('zlo','other',model)
    assert not run_role('zlo','third',model,context='other')
    for candidate in ('K','k'):
        assert not run_role('zlo',candidate,model|{'va':lambda x:True,'eisd3':lambda *xs:True})


def test_relative_speed_role_binds_frame_and_signed_speed():
    cuts,_=numbers();c=cuts.make
    norm=lambda xs:tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs)
    rows={'eja2':{('k','third',Q(-3),'context')},'s45':{(Q(5),Q(-3))}}
    model={n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()}|{
        'zbm':lambda:'k','zlo':lambda:'third','zb6':lambda:'context','tc':lambda:c(5)}
    assert perturb(lambda m:run_role('zlt',c(-3),m),model,rows,norm)
    assert not run_role('zlt',c(3),model)
    assert not run_role('zlt',c(-3),model|{'tc':lambda:c(6)})
    assert run_role('zlt',c(-3),model,context='other')


def test_past_stage_role_binds_candidate_and_current_context():
    rows={'zm4':{('earlier','reference')}};model={'zm4':relation(rows['zm4'])}
    assert perturb(lambda m:run_role('zly','earlier',m),model,rows)
    assert not run_role('zly','reference',model)
    assert not run_role('zly','earlier',model,context='other')


def test_previous_method_role_binds_program_stage_endpoints_and_steps():
    # The sequence is an opaque typed witness here; native sequence semantics
    # and nonempty connected chains are checked in the alternative-model cases.
    doc=role_fixture('zlv')
    result=next(d['result'] for d in doc['declarations'] if d['name']==mapping()['zlx'])
    sequence=SequenceValue((),check.canonical(result['element']))
    def program(method,stage):
        if (method,stage)!=('method','earlier'):return forbidden()
        return sequence
    def chain(steps,before,after,rules):
        return steps is sequence and (value(before),value(after))==('ejpb','ejpr') and rules(before,after)
    pairs={('ejpb','ejpc'),('ejpc','ejpr')}
    model={'zly':lambda:'earlier','zlx':program,'s2w':chain,
        's5h':lambda steps,a,b:steps is sequence and (value(a),value(b)) in pairs,
        'zla':lambda a,b,s:(value(a),value(b),s)==('ejpb','ejpr','earlier')}
    assert run_role('zlv','method',model)
    for name in ('s2w','s5h','zla'):
        assert not run_role('zlv','method',model|{name:lambda *xs:False})
    for pair in pairs:
        assert not run_role('zlv','method',model|{'s5h':lambda steps,a,b,pair=pair:(value(a),value(b)) in pairs-{pair}})
    for patch in ({'zly':lambda:'other'},{}):
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            run_role('zlv','method' if patch else 'other',model|patch)
    assert run_role('zlv','method',model,context='other')
