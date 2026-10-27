"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Native individual quantifiers remain in the distinguishing two-value models. Numerical cut examples and reference binding checks are diagnostics, not proofs over all real inputs.
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
from scripts import check_einstein_origin_clock_visible as check
from scripts import origin_clock_visible_profile as profile
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
    raise ValueError('Unknown clock-site-time input (origin-clock-visible fixture)')

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


from inspect import signature
from scripts import check_moving_trip_geometry as trip
from scripts import check_origin_clock_question as question
from scripts import check_origin_clock_equations as equations
from scripts import check_origin_clock_time as time
from scripts import check_clock_seconds_claim as seconds

MODULES=dict(question=question,equations=equations,time=time,seconds=seconds)
CHECKS=dict(question=('local_checks','binding_checks','capability_checks','origin_checks','comparison_checks','rate_checks','presentation_checks'),
    equations=('numeric_checks','bridge_checks','scope_checks','presentation_checks'),
    time=('time_checks','scope_checks','presentation_checks'),
    seconds=('exact_checks','pair_checks','all_interval_checks','approximation_checks','asymptotic_checks','presentation_checks'))
EXPOSE=dict(question={'ejil':1,'ejin':1,'ejip':1,'ejir':1},
    equations={},time={},seconds={'ejju':1,'ejjw':1,'svx':1,'svy':2})

@lru_cache(None)
def fixture(group,name,mode='boundary'):
    source=MODULES[group]
    blueprint,slots=source.fixture(name) if group=='equations' else source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            assert len(expose(actual,{'forall','exists'},only_sort=RS))==EXPOSE[group][name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(group,name,args,m,*rest,**kwargs):
    source=MODULES[group]
    bound=signature(source.run).bind(name,args,m,*rest,**kwargs);bound.apply_defaults()
    options=bound.arguments;doc,slots=fixture(group,name,options.get('mode','boundary'))
    assert len(args)==len(slots),(group,name,len(args),len(slots))
    point={'question':'jocqpoint','equations':'jocepoint','time':'joctpoint','seconds':'jcscpoint'}[group]
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|{point:lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=options['domain'],situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,QuestionValue=QuestionValue,
        Content=Content,SequenceValue=SequenceValue,numbers=numbers,
        forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,value=value)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models():
    norm_factory=clone(trip,('norm_factory',))['norm_factory']
    result={}
    for group,module in MODULES.items():
        extra=dict(norm_factory=norm_factory,run=lambda *args,group=group,**kwargs:run(group,*args,**kwargs))
        if group=='question':functions=('numeric','physical',*CHECKS[group])
        elif group=='equations':functions=('model',*CHECKS[group])
        else:
            extra['model']=result['equations']['model']
            functions=(('function_norm',) if group=='seconds' else ())+CHECKS[group]
        result[group]=clone(module,functions,extra)
    return result

@pytest.mark.parametrize('group,name',[(g,n) for g,ns in CHECKS.items() for n in ns])
def test_decoded_clock_distinguishing_models(group,name):assert models()[group][name]()

def test_source_backprojection_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(173,179))
    assert list(b['source_units'])==[f'einstein-1905:u{i:04d}' for i in range(118,126)]
    assert (len(doc['declarations']),len(doc['statements']))==(2351,154)
    parent=check.previous.document();assert doc['statements'][:148]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',catalog.entries[name]['meaning_ja'])
    assert len(check.vocabulary()._words)==836 and len(check.NEW_DEFINITIONS)==66
    assert b['new_public_relations']==3 and b['new_core_words']==b['new_reference_primitives']==0
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(6,122,32)

def test_uninstantiated_native_quantifiers_and_clock_identity():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for group,roots in EXPOSE.items():
        for name in roots:
            native={d['name']:d for d in fixture(group,name)[0]['declarations']}
            assert native[mapping()[name]]==ds[mapping()[name]]
    def refs(old):return set(_references(ds[mapping()[old]]['body']))
    assert {mapping()[n] for n in ('zid','ejin','ca')}<=refs('ejio')
    assert {mapping()[n] for n in ('ejip','ejir','ejit','ejis')}<=refs('ejiu')
    assert {mapping()[n] for n in ('svp','ejjd','ejiu','ejjs')}<=refs('ejjt')
    assert {mapping()[n] for n in ('ejju','svq','swc')}<=refs('ejjv')
    seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(check.reference_roles()['zie'])
    assert check.names()['zie'] not in seen
    # Keep the unit role's real existential; finite binding is tested separately.
    role=deepcopy(ds[check.reference_roles()['zik']])
    assert len(expose(role,{'exists'},only_sort=RS))==1

def test_sentence_spans_roles_and_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():
        args=[b['ri'],*map(Q,pos)];assert h['sentencereference'](*args)==b[old]
        for slot in range(3):
            bad=args[:];bad[slot]='unknown' if slot==0 else Q(999)
            with pytest.raises(ValueError):h['sentencereference'](*bad)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args[:];bad[slot]=Q(999) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        assert h['describedreference'](*args)==b[old]
        for slot in range(4):
            bad=args[:];bad[slot]='unknown'
            with pytest.raises(ValueError):h['describedreference'](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
    assert [len(row['tokens']) for row in check.text_boundaries()['sentences'].values()]==[41,10,22,33]

def test_native_references_do_not_execute_quoted_roles():
    b=check.BASE
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='clockcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('clockcapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['clockcapture']=lambda x:x==b[old]
        assert evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)[0]['value']

def role_fixture(old,boundaries,instantiate=False):
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=deepcopy(ds[check.reference_roles()[old]])
    if instantiate:assert len(expose(role,{'exists'},only_sort=RS))==1
    decls=[]
    for old in boundaries:
        d=ds[mapping()[old]];parameters=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        decls.append(dict(kind='primitive',name=d['name'],parameters=parameters,result=d['result']))
    slots=[]
    for i,param in enumerate(role['parameters']):
        n='clockroleslot'+chr(97+i);slots.append(n)
        decls.append(dict(kind='primitive',name=n,parameters=[],result=param['sort']))
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[role],
        statements=[dict(kind='ask',body=call(role['name'],*(call(n) for n in slots)))]))
    return doc,slots

def test_clock_role_shares_candidate_and_physical_context():
    doc,slots=role_fixture('zie',('ejio','ejip','zb6'))
    base={slots[0]:lambda:'clock',slots[1]:lambda:'discourse',mapping()['zb6']:lambda:'physical'}
    rows={n:{('clock','physical')} for n in ('ejio','ejip')}
    def test(model):
        handlers=base|{mapping()[n]:fn for n,fn in model.items()}
        return evaluate_document(doc,individuals=('clock','other'),situations=('physical','discourse','other'),primitives=handlers)[0]['value']
    assert perturb(test,{n:relation(rs) for n,rs in rows.items()},rows)

def test_second_unit_role_binds_one_positive_scale_to_both_units():
    doc,slots=role_fixture('zik',('ci','sbg','zil','rb','zb6'),True)
    cuts,m=numbers();c=cuts.make
    norm=clone(trip,('norm_factory',))['norm_factory'](cuts,(0,1))
    for scale in (Q(1,5),Q(1),Q(2)):
        base={slots[0]:lambda:'second',slots[1]:lambda:'discourse',slots[2]:lambda:c(scale),
            mapping()['rb']:lambda:'duration',mapping()['zb6']:lambda:'physical'}
        rows={'ci':{('duration',),('second',)},'sbg':{norm([c(scale)])},
              'zil':{norm(['duration','second',c(scale),'physical'])}}
        def test(model):
            handlers=base|{mapping()[n]:fn for n,fn in model.items()}
            return evaluate_document(doc,individuals=('duration','second','other'),situations=('physical','discourse','other'),primitives=handlers)[0]['value']
        assert perturb(test,{n:lambda *xs,rs=rs:norm(xs) in rs for n,rs in rows.items()},rows,norm)
    # svp's actual positive-cut condition is exercised by exact_checks above;
    # this role diagnostic checks its shared binding without sampling existence.
