"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. Sentence references are checked separately. The old ejpr implication is
retained only as a diagnostic comparator outside the migrated selection. Native individual quantifiers remain in the distinguishing two-value models. Numerical cut examples and reference binding checks are diagnostics, not proofs over all real inputs.
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
from scripts import check_einstein_velocity_axial_visible as check
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
    raise ValueError('Unknown clock-site-time input (velocity-axial-visible fixture)')

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


from scripts import check_velocity_axial_claim as axial
from scripts import check_velocity_composition_claim as composition

CHECKS=('numeric_checks','symmetry_checks','appraisal_checks','physical_checks','presentation_checks')


@lru_cache(None)
def fixture(name,mode='boundary'):
    blueprint,slots=axial.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        if d['name']=='ejpr':
            # The old conditional comparator is not part of the selected
            # author-attributed consequence. Its two contents are decoded.
            assert name=='ejpr' and _references(d['body'])=={mapping()['ejpp'],mapping()['ejpq']}
            continue
        assert d['name'] in decoded,(name,d['name'])
        actual=deepcopy(decoded[d['name']])
        if name=='s3a' and mode=='instance' and d['name']==mapping()[name]:
            assert len(expose(actual,{'forall'},only_sort=RS))==3
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,m,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in axial.CONSTANTS.items()}|{'jvacpoint':lambda:'discourse'}|m|{n:lambda x=x:x for n,x in zip(slots,args,strict=True)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=axial.DOMAIN,situations=axial.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=3000000,memoize_definitions=True,memoize_expressions=True)[0]['value']


def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value,SemanticError=ValueError)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns


@lru_cache(None)
def models():
    arithmetic=clone(composition,('arithmetic',))['arithmetic']
    return clone(axial,CHECKS,dict(arithmetic=arithmetic,run=run))


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_axial_distinguishing_models(name):assert models()[name]()


def test_source_order_parent_and_public_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[5,6,7]
    assert list(b['source_units'])==['einstein-1905:u0141','einstein-1905:u0142']
    assert len(doc['statements'])==175
    parent=check.previous.document();assert doc['statements'][:172]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    current=check.vocabulary().document();prior=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==row for n,row in prior[field].items())
    catalog=check.catalogs()['einstein-1905'];old={d['name']:d for d in check.source_excerpt()['declarations']}
    for name,public in check.PUBLIC_RELATIONS.items():
        contract=profile.CONTRACTS[public]
        assert (contract['parameters'],contract['result'])==(old[name]['parameters'],old[name]['result'])
        assert contract['arguments']==catalog.entries[name]['arguments']
        assert contract['meaning_ja']==re.sub(r'^\[[^]]+ の記号名\] ','',catalog.entries[name]['meaning_ja'])
    assert len(check.vocabulary()._words)==861 and len(check.NEW_DEFINITIONS)==17
    assert (b['new_public_relations'],b['new_core_words'],b['new_reference_primitives'])==(2,0,0)
    assert (b['new_source_assertions'],b['total_source_assertions'],b['total_annotations'])==(3,143,32)
    assert all(ds[mapping()[n]]==renamed(old[n],mapping()) for n in check.NEW_DEFINITIONS)


def test_sentence_positions_and_unknown_inputs():
    b=dict(check.BASE);h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():
        args=[b['ri'],*map(Q,pos)]
        assert h['sentencereference'](*args)==b[old]
        for slot in range(3):
            bad=args[:];bad[slot]='unknown' if slot==0 else Q(999)
            with pytest.raises(ValueError):h['sentencereference'](*bad)
    assert [len(r['tokens']) for r in check.text_boundaries()['sentences'].values()]==[18,12]


def test_native_sentence_references_do_not_execute_claims():
    b=dict(check.BASE)
    for old in check.SENTENCES:
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='axialcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('axialcapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()})
        handlers['axialcapture']=lambda x:x==b[old]
        declared={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
        assert evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,
            primitives={n:handlers[n] for n in declared})[0]['value']
