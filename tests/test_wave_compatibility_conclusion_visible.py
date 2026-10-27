"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. The original finite input models remain bounded diagnostics. Old verdicts and
caches are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from math import isqrt
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_wave_compatibility_conclusion_visible as check
from scripts import wave_compatibility_conclusion_visible_profile as profile
from scripts import check_wave_compatibility_conclusion as source
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (wave-compatibility-conclusion-visible fixture)')

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


CHECKS=('propagation_checks','wave_checks','argument_checks','compatibility_checks','presentation_checks')

@lru_cache(None)
def fixture(name):
    old,slots=source.fixture(name)
    doc=normalize_document(renamed(deepcopy(old),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert actual['kind']=='definition'
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']] and actual['result']==d['result']
        doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(name,args,model,domain=source.DOMAIN,point='discourse'):
    doc,slots=fixture(name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jwccpoint':lambda:point}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    handlers={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=domain,situations=source.POINTS,primitives=handlers,
        max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

@lru_cache(None)
def models():
    ns=dict(vars(source))|dict(FunctionValue=FunctionValue,Content=Content,numbers=numbers,
        forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,run=run)
    for name in ('propagation_model',*CHECKS):
        original=getattr(source,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()

def test_source_backprojection_and_parent_preservation():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[143,144]
    assert list(b['source_units'])==['einstein-1905:u0091'] and [r['id'] for r in b['math']]==['M0147']
    assert b['text_boundaries']['spans']=={'zgf':['movingwaveconclusionsentence',1,16],'zgg':['compatibilityprovedsentence',1,10]}
    assert len(check.NEW_DEFINITIONS)==11
    assert not {'sqz','shd','smk','sqn','sqv','sqw','spk'}&set(check.mapping())
    parent=check.previous.document();assert doc['statements'][:113]==parent['statements']
    old={d['name']:d for d in parent['declarations']};new={d['name']:d for d in doc['declarations']}
    assert all(new[n]==d for n,d in old.items()) and len(new)-len(old)==16
    assert len(doc['declarations'])==1836 and len(doc['statements'])==115
    assert b['reference_roles']=={} and b['forwarded_reference_signatures']=={}

def test_preserved_public_proof_status_and_profile():
    vocabulary=check.vocabulary();assert len(vocabulary._words)==788
    before=check.previous.vocabulary().document();after=vocabulary.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(after[field].get(n)==d for n,d in before[field].items())
    assert profile.SOURCE_RELATIONS=={'ui':'presentsasproved'}
    contract=profile.CONTRACTS['presentsasproved'];assert contract['arguments']==['author','node','context']
    source_decl=next(d for d in check.source_excerpt()['declarations'] if d['name']=='ui')
    native=next(d for d in check.restored()['document']['declarations'] if d['name']==check.mapping()['ui'])
    assert native['kind']=='primitive' and native['parameters']==source_decl['parameters']==contract['parameters']
    assert native['result']==source_decl['result']==contract['result']=='truth'

def test_both_whole_sentence_spans_and_scope_arguments():
    b=check.BASE;h=check.context_handlers(b)
    for reference,(sentence,start,end) in check.SPANS.items():
        node=b[sentence];args=[b['eirf'],node,Q(start),node,Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[reference]
        for slot in range(len(args)):
            bad=args.copy();bad[slot]=Q(2 if slot==2 else end-1) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
        paragraph,item=check.SENTENCES[sentence]
        assert h['sentencereference'](b['ri'],Q(paragraph),Q(item))==node
        with pytest.raises(ValueError):h['sentencereference']('unknown',Q(paragraph),Q(item))
    with pytest.raises(ValueError):h['sentencereference'](b['ri'],Q(47),Q(3))

def test_native_references_do_not_execute_the_asserted_conclusions():
    doc=deepcopy(check.restored()['document']);b=check.BASE
    doc['declarations'].append(dict(kind='primitive',name='conclusioncapture',parameters=['individual','individual'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('conclusioncapture',call(check.names()['zgf']),call(check.names()['zgg'])))]
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    h|={check.vocabulary()._symbols[n]:fn for n,fn in check.context_handlers(b).items()}
    h['conclusioncapture']=lambda first,second:(first,second)==(b['zgf'],b['zgg'])
    assert [r['value'] for r in evaluate_document(doc,individuals=tuple(set(b.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=h)]==[True]
