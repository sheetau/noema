"""Check recovered Native definitions, real-domain boundaries and nonexecuting references.

Preserved models supply distinguishing inputs. All tested definitions are replaced
by recovered Native bodies before explicit instantiation. Two-value record tests
diagnose argument binding; they do not prove all real times or physical histories.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_transverse_endpoint_claim_visible as check
from scripts import transverse_endpoint_claim_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_transverse_endpoint_claim as endpoint
from scripts import check_transverse_segment as segment
from scripts.check_translated_light_trial import expose
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (four-coordinate-visible fixture)')

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

MODULES=dict(endpoint=endpoint,segment=segment)
CHECKS=[('endpoint',n) for n in ('numeric_checks','scope_checks','presentation_checks')]+[('segment',n) for n in ('segment_checks','history_checks','motion_checks','record_checks')]


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    blueprint,slots=MODULES[group].fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            assert len(expose(actual,{'forall'},only_sort=RS))==1
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,args,model,mode='boundary',domain=None):
    source=MODULES[group];doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jtecpoint',lambda:'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN if domain is None else domain,situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,arithmetic=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models(group):
    names=tuple(n for g,n in CHECKS if g==group)
    execute=lambda name,args,m,mode='boundary',domain=None:run(group,name,args,m,mode,domain)
    if group=='endpoint':return clone(endpoint,names,dict(previous_model=clone(four,('model',))['model'],run=execute))
    return clone(segment,('model',*names),dict(run=execute))


@pytest.mark.parametrize('group,name',CHECKS)
def test_decoded_native_distinguishing_models(group,name):assert models(group)[name]()


def test_source_backprojection_and_preserved_parent():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[151,152,153]
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(97,101)]
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(170,181)]
    assert len(doc['declarations'])==1959 and len(doc['statements'])==129
    parent=check.previous.document();assert doc['statements'][:126]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.NEW_DEFINITIONS)==27 and b['new_public_relations']==2 and b['new_reference_primitives']==0


def test_public_contracts_and_previous_profile_preserved():
    voc=check.vocabulary();assert len(voc._words)==798
    before=check.previous.vocabulary().document();after=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(after[field][n]==d for n,d in before[field].items())
    assert len(profile.SOURCE_RELATIONS)==2
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        original=next(d for d in check.source_excerpt()['declarations'] if d['name']==old)
        actual=ds[mapping()[old]];contract=profile.CONTRACTS[new]
        assert actual['kind']=='primitive' and actual['parameters']==original['parameters']==contract['parameters']
        assert actual['result']==original['result']=='truth'


def test_sentence_and_display_span_coordinates_reject_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():assert h['sentencereference'](b['ri'],*map(Q,pos))==b[old]
    for args in ((b['ri'],Q(51),Q(4)),('unknown',Q(51),Q(1)),(b['ri'],Q(0),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args.copy();bad[slot]=Q(99) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
        if start<end:
            bad=args.copy();bad[2]=Q(end);bad[4]=Q(start)
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    boundary=check.text_boundaries();sentences=boundary['sentences']
    assert [len(s['tokens']) for s in sentences.values()]==[8,18,30]
    assert sentences['endpointdisplays']['tokens'][27:]==['[M0179]','und','[M0180]']


def checked_values():
    cuts,_=numbers();return cuts,check.BASE|dict(zgz=cuts.make(Q(2)))


def evaluate_reference(old):
    cuts,b=checked_values();doc=deepcopy(check.restored()['document'])
    sort=profile.CUT if old=='zgz' else 'individual'
    doc['declarations'].append(dict(kind='primitive',name='endpointreferencecapture',parameters=[sort],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('endpointreferencecapture',call(check.names()[old])))]
    handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
    handlers['endpointreferencecapture']=lambda x:cuts.read(x)==Q(2) if old=='zgz' else x==b[old]
    result=evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
    assert [r['value'] for r in result]==[True]


def test_native_text_and_role_references_do_not_execute_contents():
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):evaluate_reference(old)


def test_role_reference_argument_scope_types_and_unknown_inputs():
    cuts,b=checked_values();handlers=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        sort=profile.CUT if old=='zgz' else 'individual';kind='describedcutreference' if old=='zgz' else 'describedreference'
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        actual=handlers[kind](*args)
        assert cuts.read(actual)==Q(2) if old=='zgz' else actual==b[old]
        for slot in range(4):
            bad=args.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):handlers[kind](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):handlers[kind](*args[:2],bad,args[3])


def test_native_closed_roles_bind_the_same_segment_and_candidate_slot():
    from itertools import product
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    cuts,b=checked_values();constants={'zgu':'a','zgv':'b','zgw':'a','zb6':'context','zgz':b['zgz']}
    body=decoded[mapping()['ejcc']]
    boundary=dict(kind='primitive',name=body['name'],parameters=[p['sort'] for p in body['parameters']],result=body['result'])
    for old,slot,witnesses in [('zgu',0,(1,2)),('zgv',1,(2,)),('zgw',2,())]:
        role=deepcopy(decoded[check.reference_roles()[old]])
        ds=[role,boundary]+[dict(kind='primitive',name=check.names()[n],parameters=[],result=profile.CUT if n=='zgz' else 'situation' if n=='zb6' else 'individual') for n in constants]
        ds+=[dict(kind='primitive',name='endpointcandidate',parameters=[],result='individual'),dict(kind='primitive',name='endpointcontext',parameters=[],result='situation')]
        ds.sort(key=lambda d:d['kind']!='primitive')
        doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[dict(kind='ask',body=call(role['name'],call('endpointcandidate'),call('endpointcontext')))]))
        expected=['a','b','a','context',Q(2)];expected[slot]='a'
        norm=lambda xs:tuple(cuts.read(x) if isinstance(x,FunctionValue) else x for x in xs)
        handlers={check.names()[n]:lambda x=x:x for n,x in constants.items()}|dict(endpointcandidate=lambda:'a',endpointcontext=lambda:'discourse')
        def execute(row,changes=None):
            result=evaluate_document(doc,individuals=('a','b'),situations=('context','discourse','other'),primitives=handlers|{boundary['name']:lambda *xs:norm(xs)==tuple(row)}|(changes or {}))
            return result[0]['value']
        # Actual existential bodies, two values in every witness slot.
        for values in product(('a','b'),repeat=len(witnesses)):
            row=expected.copy()
            for i,x in zip(witnesses,values):row[i]=x
            assert execute(row)
        for i in range(5):
            bad=expected.copy();bad[i]=Q(99) if i==4 else 'other' if i==3 else 'wrong' if i in witnesses else 'b' if bad[i]=='a' else 'a'
            assert not execute(bad)
        assert execute(expected,dict(endpointcontext=lambda:'other'))
        with pytest.raises(ValueError):execute(expected,{boundary['name']:forbidden})
    extent=deepcopy(decoded[check.reference_roles()['zgz']])
    assert extent['body']==call(mapping()['sbg'],dict(kind='variable',name=extent['parameters'][0]['name']))
    assert not (_references(extent['body']) & {check.names()[n] for n in ('zgu','zgv','zgw','zgz')})
    ds=[extent,dict(kind='primitive',name=mapping()['sbg'],parameters=[profile.CUT],result='truth'),
        dict(kind='primitive',name='extentcandidate',parameters=[],result=profile.CUT),
        dict(kind='primitive',name='extentcontext',parameters=[],result='situation')]
    ds.sort(key=lambda d:d['kind']!='primitive')
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[dict(kind='ask',body=call(extent['name'],call('extentcandidate'),call('extentcontext')))]))
    for candidate in (Q(-2),Q(0),Q(2)):
        result=evaluate_document(doc,individuals=('a','b'),situations=('discourse',),primitives={mapping()['sbg']:lambda x:cuts.read(x)>0,'extentcandidate':lambda:cuts.make(candidate),'extentcontext':lambda:'discourse'})
        assert result[0]['value']==(candidate>0)
