"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. Reference
forwarding and the actual map pair are checked separately. Old verdicts and
caches are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_transverse_ray_visible as check
from scripts import transverse_ray_visible_profile as profile
from scripts import check_transverse_ray_claim as source
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (transverse-ray-visible fixture)')

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

@lru_cache(None)
def fixture(name,mode='boundary'):
    blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(name,args,model,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jtrcpoint',lambda:'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    h={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=('context','discourse','other'),
        primitives=h,max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone_models(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value,run=run)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

CHECKS=('path_checks','trace_checks','connection_checks','equation_checks','presentation_checks')

@lru_cache(None)
def models():
    return clone_models(source,('model',*CHECKS))

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):
    assert models()[name]()

def test_source_backprojection_and_preserved_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==list(range(131,136))
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(73,81)]
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(130,134)]
    assert [len(s['tokens']) for s in b['text_boundaries']['sentences'].values()]==[22]
    assert b['sentence_coordinates']=={'transverseraysentence':[42,1]}
    assert len(check.NEW_DEFINITIONS)==31 and len(check.vocabulary()._words)==778
    assert doc['statements'][:101]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert not profile.CONTRACTS and len(profile.EXTRA)==1
    assert set(b['forwarded_reference_signatures'])=={'zfa','zfb'}
    assert all(d['kind']=='primitive' and d['parameters']==['individual'] and d['result']=='individual'
               for d in b['forwarded_reference_signatures'].values())


def context(doc,values=None):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{
        check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE if values is None else values).items()}


def evaluate(doc,h):
    # The inherited frame designation traverses two explicit reference nodes.
    # These are part of its finite fixture domain, even though they are not BASE fields.
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),
        situations=check.SITUATIONS,primitives=h)]


def description(old):
    return DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(profile.ROLE))


def finite_map(table):
    def get(axis):
        if axis not in table:forbidden()
        return table[axis]
    return FunctionValue(('individual',),'individual',get)


def map_values():
    b=check.BASE
    return b|dict(transverserestmap=finite_map({b['yo']:b['transverseresty'],b['yp']:b['transverserestz']}),
                  transversemovingmap=finite_map({b['yo']:b['transversemovingy'],b['yp']:b['transversemovingz']}))


def test_function_reference_types_roles_scopes_and_nonexecution():
    b=check.BASE
    # Merely obtaining these references must not call either function.
    values=b|{old:FunctionValue(('individual',),'individual',forbidden) for old in check.ROLE_ASSIGNMENTS}
    h=check.context_handlers(values)['describedindividualfunctionreference']
    for old in check.ROLE_ASSIGNMENTS:
        key=[b['eirf'],b[check.reference_anchor(old)],description(old),b['ri']]
        assert h(*key) is values[old]
        for slot in range(4):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h(*bad)
        for badrole in (DescriptionValue('{}',key[2].result_type),DescriptionValue(key[2].syntax,'"individual"'),DescriptionValue(key[2].syntax,key[2].result_type,1)):
            with pytest.raises(ValueError):h(*key[:2],badrole,key[3])
        other=next(n for n in check.ROLE_ASSIGNMENTS if n!=old)
        assert h(*key[:2],description(other),key[3]) is values[other]
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='transversecapturemap',parameters=[profile.MAP],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('transversecapturemap',call(check.names()[old])))]
        assert evaluate(doc,context(doc,values)|dict(transversecapturemap=lambda fn:fn.parameters==('individual',) and fn.result=='individual'))==[True]
    for invalid in ('not a function',FunctionValue(('number',),'individual',lambda n:'x'),
                    FunctionValue(('individual',),'truth',lambda n:True),FunctionValue(('individual',),'individual',None)):
        with pytest.raises(ValueError):profile.IndividualFunctionReferences({('d','n','role','c'):invalid})


def test_native_forward_maps_preserve_the_selected_axis_and_reject_unknowns():
    b=check.BASE;values=map_values()
    for old,prefix in (('zfa','transverserest'),('zfb','transversemoving')):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'] += [dict(kind='primitive',name='transverseprobeaxis',parameters=[],result='individual'),
                                dict(kind='primitive',name='transversecapture',parameters=['individual'],result='truth')]
        doc['statements']=[dict(kind='ask',body=call('transversecapture',call(check.names()[old],call('transverseprobeaxis'))))]
        for axis,suffix in (('yo','y'),('yp','z')):
            h=context(doc,values)|dict(transverseprobeaxis=lambda axis=axis:b[axis],transversecapture=lambda x,suffix=suffix:x==b[prefix+suffix])
            assert evaluate(doc,h)==[True]
            with pytest.raises(ValueError,match='Unknown clock-site-time'):
                evaluate(doc,h|dict(transverseprobeaxis=lambda:'other'))


def test_sentence_and_span_references_preserve_all_five_parts():
    b=check.BASE;h=check.context_handlers(b)
    assert h['sentencereference'](b['ri'],42,1)==b['transverseraysentence']
    for key in ((b['ri'],42,2),(b['ri'],42,Q(1,2)),('unknown',42,1)):
        with pytest.raises(ValueError):h['sentencereference'](*key)
    for old,(node,first,last) in check.SPANS.items():
        key=[b['eirf'],b[node],first,b[node],last,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='transversecapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('transversecapture',call(check.names()[old])))]
        assert evaluate(doc,context(doc)|dict(transversecapture=lambda x:x==b[old]))==[True]
    assert h['sentencereference'](b['ri'],41,1)==b['ze6']


def test_whole_five_attributions_preserve_order_and_nonfactivity():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][101:106];b=check.BASE
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for _,message,_,node,_ in source.GROUPS},
          'ue':{(b[previous],b[node],b['ri']) for _,_,_,node,previous in source.GROUPS}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    # There are no map references registered here: quoted physics must stay quoted.
    assert evaluate(doc,h)==[True]*5
    for n,rs in rows.items():
        for row in rs:
            result=evaluate(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==4


def role_probe(old,candidate,rows):
    doc=deepcopy(check.restored()['document']);m=mapping();target=check.reference_roles()[old]
    for d in doc['declarations']:
        if d['name'] in {m['ei6d'],m['yo'],m['yp'],m['zb6']}:
            if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
            d['kind']='primitive';d.pop('body',None)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(target);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    for name,sort in (('transverseprobecandidate',profile.MAP),('transverseprobecontext','situation')):
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=sort))
    doc['statements']=[dict(kind='ask',body=call(target,call('transverseprobecandidate'),call('transverseprobecontext')))]
    h={m['yo']:lambda:'a',m['yp']:lambda:'b',m['zb6']:lambda:'physical',m['ei6d']:lambda *xs:xs in rows,
       'transverseprobecandidate':lambda:candidate,'transverseprobecontext':lambda:'discourse'}
    return evaluate_document(doc,individuals=('a','b'),situations=('physical','discourse','other'),primitives=h)[0]['value']


def test_native_closed_roles_bind_both_axes_with_independent_witnesses():
    candidate=finite_map({'a':'a','b':'b'})
    for old,fixed in (('transverserestmap',0),('transversemovingmap',1)):
        rows={('a','b','a','physical'),('b','a','b','physical')} if fixed==0 else {('b','a','a','physical'),('a','b','b','physical')}
        assert role_probe(old,candidate,rows)
        assert not role_probe(old,finite_map({'a':'a','b':'a'}),rows)
        for row in rows:
            assert not role_probe(old,candidate,rows-{row})
            for slot in (fixed,2,3):
                bad=tuple(('other' if slot==3 else ('b' if x=='a' else 'a')) if i==slot else x for i,x in enumerate(row))
                assert not role_probe(old,candidate,(rows-{row})|{bad})
            # The opposite slot is existential: a different available witness is valid.
            slot=1-fixed
            changed=tuple(('b' if x=='a' else 'a') if i==slot else x for i,x in enumerate(row))
            assert role_probe(old,candidate,(rows-{row})|{changed})


def test_actual_reference_pair_is_required_beyond_separate_roles():
    b=check.BASE;values=map_values();doc=deepcopy(check.restored()['document']);target=mapping()['ei6d']
    for d in doc['declarations']:
        if d['name']==target:
            d['kind']='primitive';d['parameters']=[p['sort'] for p in d['parameters']];d.pop('body')
    doc['statements']=[dict(kind='ask',body=dict(kind='evaluate',content=call(mapping()['ei6f']),situation=call(check.names()['ri'])))]
    rows={(b['transverseresty'],b['transversemovingy'],b['yo'],b['zb6']),
          (b['transverserestz'],b['transversemovingz'],b['yp'],b['zb6'])}
    h=context(doc,values)|{target:relation(rows)}
    assert evaluate(doc,h)==[True]
    for row in rows:
        for slot in range(4):
            changed=tuple('other' if i==slot else x for i,x in enumerate(row))
            assert evaluate(doc,h|{target:relation((rows-{row})|{changed})})==[False]
    # Lookup still succeeds, but the two actual maps no longer form the required pair.
    wrong=values|dict(transversemovingmap=finite_map({b['yo']:b['transversemovingz'],b['yp']:b['transversemovingy']}))
    assert evaluate(doc,context(doc,wrong)|{target:relation(rows)})==[False]
