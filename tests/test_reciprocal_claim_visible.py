"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Record diagnostics use two target
values and a third frame individual required by typing, preserving nonempty domains
and aliases. These are binding diagnostics, not proofs over the full domain.
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
from scripts import check_einstein_reciprocal_claim_visible as check
from scripts import third_frame_claim_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_reciprocal_claim as source
from scripts import check_first_principle as first
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

CHECKS=('numeric_checks','rest_checks','scope_checks','presentation_checks')

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


def run(name,args,model,domain=source.DOMAIN,points=source.POINTS,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jrcppoint',lambda:'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=domain,situations=points,
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
def models():
    base=clone(four,('model',));frame=clone(first,('frame_model',))
    return clone(source,CHECKS,dict(previous_model=base['model'],frame_model=frame['frame_model'],run=run))


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_parent_and_unchanged_vocabulary():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[148,149,150]
    assert list(b['source_units'])==['einstein-1905:u0095','einstein-1905:u0096']
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(162,170)]
    assert len(doc['declarations'])==1916 and len(doc['statements'])==126
    parent=check.previous.document();assert doc['statements'][:123]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==796 and len(check.NEW_DEFINITIONS)==16
    assert b['new_public_relations']==b['new_reference_primitives']==0


def test_spatial_rhs_excludes_time_and_native_rest_preserves_motion_body():
    ds={d['name']:d for d in check.restored()['document']['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(mapping()['ejbr']);assert mapping()['zc7'] not in seen
    doc,_=fixture('ejbq','native');actual={d['name']:d for d in doc['declarations']}
    for name in ('ejbq','eioj','eioi'):
        assert actual[mapping()[name]]==ds[mapping()[name]]
    boundary,_=fixture('ejbq');boundary={d['name']:d for d in boundary['declarations']}
    assert boundary[mapping()['eioj']]['kind']=='primitive'


def test_sentence_and_partial_span_coordinates_reject_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():
        assert h['sentencereference'](b['ri'],*map(Q,pos))==b[old]
    for args in ((b['ri'],Q(50),Q(3)),('unknown',Q(50),Q(1)),(b['ri'],Q(0),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args.copy();bad[slot]=Q(99) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
        bad=args.copy();bad[2]=Q(end);bad[4]=Q(start)
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    boundaries=check.text_boundaries();sentences=boundaries['sentences']
    assert [len(s['tokens']) for s in sentences.values()]==[35,4]
    assert sentences['reciprocalpremises']['tokens'][4]=='[M0162]und'
    assert sentences['reciprocalpremises']['tokens'][19:23]==['und','es','ist','klar,']
    assert sentences['zgs']['text']=='Es ist also: [M0169].'


def test_native_text_references_do_not_execute_their_claims():
    b=check.BASE
    for old in (*check.SENTENCES,*check.SPANS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='reciprocalreferencecapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('reciprocalreferencecapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
        handlers['reciprocalreferencecapture']=lambda x:x==b[old]
        result=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
        assert [r['value'] for r in result]==[True]
