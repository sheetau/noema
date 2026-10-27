"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. Stage
references and their closed roles are checked separately. Explicitly instantiated
function bodies remain bounded diagnostics. Old verdicts are not reused.
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
from scripts import check_einstein_phi_determination_intent_visible as check
from scripts import phi_determination_intent_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_phi_determination_intent as source
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

CHECKS=('candidate_checks','continuation_checks','presentation_checks')

def expose(actual):
    added=[]
    def walk(node):
        if isinstance(node,list):return [walk(x) for x in node]
        if not isinstance(node,dict):return node
        if node.get('kind') in ('forall','exists'):
            added.append(dict(name=node['variable'],sort=node['sort']));return walk(node['body'])
        return {k:walk(v) for k,v in node.items()}
    actual['body']=walk(actual['body']);actual['parameters']+=added;return len(added)

@lru_cache(None)
def fixture(name,mode='boundary'):
    blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            assert expose(actual)=={'srp':2,'smq':1,'smb':3}[name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(name,args,model,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}|{'jpdipoint':lambda:'discourse'}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models():
    base=clone(four,('model',))
    return clone(source,('model','capture',*CHECKS),dict(previous_model=base['model'],run=run))

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()

def test_complete_source_backprojection_and_parent_preservation():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[145]
    assert list(b['source_units'])==['einstein-1905:u0092'] and [r['id'] for r in b['math']]==['M0148','M0149']
    sentence=b['text_boundaries']['sentences']['phideterminationsentence']
    assert sentence['position']==[48,1] and len(sentence['tokens'])==18
    assert b['text_boundaries']['spans']=={'zgt':['phideterminationsentence',1,13],'zgn':['phideterminationsentence',14,18]}
    assert len(doc['declarations'])==1847 and len(doc['statements'])==116
    parent=check.previous.document();assert doc['statements'][:115]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.NEW_DEFINITIONS)==5 and b['reference_anchors']=={'zgl':'zgn'}

def test_public_intention_contract_and_previous_profile_preserved():
    voc=check.vocabulary();assert len(voc._words)==789
    before=check.previous.vocabulary().document();after=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(after[field][n]==d for n,d in before[field].items())
    assert profile.SOURCE_RELATIONS=={'zgm':'presentsfunctiondeterminationintent'}
    contract=profile.CONTRACTS['presentsfunctiondeterminationintent']
    assert contract['arguments']==['node','author','function_description','stage','scope','context']
    old=next(d for d in check.source_excerpt()['declarations'] if d['name']=='zgm')
    actual=next(d for d in check.restored()['document']['declarations'] if d['name']==mapping()['zgm'])
    assert actual['kind']=='primitive' and actual['parameters']==old['parameters']==contract['parameters']
    assert actual['result']==old['result']=='truth'

def test_current_uncertainty_preserves_every_condition_except_stage():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    prior=renamed(deepcopy(ds[check.names()['sqd']]),{check.names()['sqd']:check.names()['srp'],check.names()['zfm']:check.names()['zgl']})
    assert prior==ds[check.names()['srp']]

def context(doc):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def evaluate(doc,handlers):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=handlers)]

def test_stage_reference_scope_types_and_nonexecution():
    b=check.BASE;h=check.context_handlers(b)
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['zgl'])),check.canonical(dict(kind='function',parameters=['situation','situation'],result='truth')))
    args=[b['eirf'],b['zgn'],role,b['ri']]
    assert h['describedsettingreference'](*args)==b['zgl']!=b['zfm']
    for slot in range(4):
        bad=args.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['describedsettingreference'](*bad)
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h['describedsettingreference'](*args[:2],bad,args[3])
    doc=deepcopy(check.restored()['document'])
    doc['declarations'].append(dict(kind='primitive',name='intentstagecapture',parameters=['situation'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('intentstagecapture',call(check.names()['zgl'])))]
    assert evaluate(doc,context(doc)|dict(intentstagecapture=lambda x:x==b['zgl']))==[True]

def test_native_stage_role_binds_same_function_candidate_stage_and_context():
    b=check.BASE;doc=deepcopy(check.restored()['document'])
    for name in ('intentstageprobe','intentcontextprobe'):
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result='situation'))
    doc['statements']=[dict(kind='ask',body=call(check.names()['phideterminationstagerole'],call('intentstageprobe'),call('intentcontextprobe')))]
    expected=(b['zgn'],b['rd'],'spc',b['zgl'],b['eisms'],b['ri'])
    h=context(doc)|{check.vocabulary()._symbols['presentsfunctiondeterminationintent']:lambda *xs:tuple(value(x) for x in xs)==expected,
        'intentstageprobe':lambda:b['zgl'],'intentcontextprobe':lambda:b['ri']}
    assert evaluate(doc,h)==[True]
    assert evaluate(doc,h|{'intentstageprobe':lambda:b['zfm']})==[False]
    assert evaluate(doc,h|{'intentcontextprobe':lambda:b['zfm']})==[False]

def test_clause_spans_all_arguments_and_sentence_coordinates():
    b=check.BASE;h=check.context_handlers(b)
    for old,(node,start,end) in check.SPANS.items():
        args=[b['eirf'],b[node],Q(start),b[node],Q(end),b['ri']]
        assert h['sentencetokenspanreference'](*args)==b[old]
        for slot in range(6):
            bad=args.copy();bad[slot]=Q(start+1 if slot==2 else end-1) if slot in (2,4) else 'unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencereference'](b['ri'],Q(48),Q(1))==b['phideterminationsentence']
    for args in ((b['ri'],Q(48),Q(2)),('unknown',Q(48),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
