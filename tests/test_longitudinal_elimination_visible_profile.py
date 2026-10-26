"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. The two
real binders are exposed only for labeled diagnostics. Old verdicts and caches
are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_longitudinal_elimination_visible as check
from scripts import longitudinal_elimination_visible_profile as profile
from scripts import check_frame_light_law as frame
from scripts import check_origin_light_ray as ray
from scripts import check_longitudinal_elimination as source
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (longitudinal-elimination-visible fixture)')

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
        if name=='ei5x' and mode=='instance' and d['name']==mapping()[name]:
            added=[]
            def expose(node):
                if isinstance(node,list):return [expose(x) for x in node]
                if not isinstance(node,dict):return node
                if node.get('kind')=='forall':
                    added.append(dict(name=node['variable'],sort=node['sort']))
                    return expose(node['body'])
                return {k:expose(v) for k,v in node.items()}
            actual['body']=expose(actual['body']);assert len(added)==2
            actual['parameters']+=added
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(name,args,model,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jlelpoint',lambda:'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    h={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=source.POINTS,
        primitives=h,max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone_models(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value,run=run)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

CHECKS=('relative_checks','origin_join_checks','elimination_checks','presentation_checks')

@lru_cache(None)
def models():
    a=clone_models(frame,('model','relations'))
    b=clone_models(ray,('model','relations'),dict(base_model=a['model']))
    return clone_models(source,('model',*CHECKS),dict(base_model=b['model']))

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):
    assert models()[name]()

def test_source_backprojection_and_preserved_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[129,130]
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(69,73)]
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(124,130)]
    assert [len(s['tokens']) for s in b['text_boundaries']['sentences'].values()]==[23,16]
    assert b['sentence_coordinates']=={'ze5':[40,1],'ze6':[41,1]}
    assert len(check.NEW_DEFINITIONS)==18 and len(check.vocabulary()._words)==777
    assert doc['statements'][:99]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    contract=profile.CONTRACTS[profile.SOURCE_RELATIONS['eisnp']]
    assert contract['parameters']==ds['eisnp']['parameters'] and contract['result']==ds['eisnp']['result']
    assert len(contract['arguments'])==8

def context(doc):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{
        check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def evaluate(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),
        situations=check.SITUATIONS,primitives=h)]

def test_sentence_references_and_unknown_boundaries():
    h=check.context_handlers(check.BASE);b=check.BASE
    for old,(paragraph,sentence) in check.SENTENCES.items():
        key=[b['ri'],paragraph,sentence]
        assert h['sentencereference'](*key)==b[old]
        for slot,badvalue in ((0,'unknown'),(1,10000),(2,10000),(1,0),(2,Q(1,2))):
            bad=key.copy();bad[slot]=badvalue
            with pytest.raises(ValueError):h['sentencereference'](*bad)
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='longitudinalcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('longitudinalcapture',call(check.names()[old])))]
        assert evaluate(doc,context(doc)|dict(longitudinalcapture=lambda x:x==b[old]))==[True]
    assert h['sentencereference'](b['ri'],39,1)==b['spatialmethodsentence']
    assert h['sentencetokenspanreference'](b['eirf'],b['spatialraysentence'],15,b['spatialraysentence'],16,b['ri'])==b['ze4']

def test_whole_two_attributions_preserve_contrast_and_substitution_order():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][99:101];b=check.BASE
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('ze5','ei53'),('ze6','ei57'))},
          'ue':{(b[first],b[last],b['ri']) for first,last in (('ze4','ze5'),('ze5','ze6'))}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert evaluate(doc,h)==[True]*2
    for n,rs in rows.items():
        for row in rs:
            result=evaluate(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==1
