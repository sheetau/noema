"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition; synthetic
finite programs remain fixture inputs. Old verdicts and caches are not reused.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_spatial_method_visible as check
from scripts import spatial_method_visible_profile as profile
from scripts import check_frame_light_law as frame
from scripts import check_origin_light_ray as ray
from scripts import check_spatial_method_claim as method
from scripts.shared_modality import call,renamed
from noema.meaning_catalog import _references

RS=profile.CUT

@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()

def forbidden(*xs):
    # Preserve the diagnostic expected by the reused frame model.
    raise ValueError('Unknown clock-site-time input (spatial-method-visible fixture)')

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

def pair(step):
    desc=dict(kind='description',result='content')
    return tuple(value(step(FunctionValue((desc,desc),desc,lambda left,right,i=i:(left,right)[i]))) for i in (0,1))

@lru_cache(None)
def fixture(group,name,mode='boundary'):
    old={'frame':frame,'ray':ray,'method':method}[group]
    blueprint,slots=old.fixture(name) if group=='frame' else old.fixture(name,mode)
    native=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    # zlx can be a synthetic finite program in the blueprint. It is a
    # primitive in the source, so its fixture definition is intentionally kept.
    reverse={v:k for k,v in mapping().items()}
    for i,d in enumerate(native['declarations']):
        oldname=reverse.get(d['name'],d['name'])
        if d['kind']=='definition' and oldname!='zlx':
            assert d['name'] in decoded,oldname
            actual=deepcopy(decoded[d['name']])
            assert [p['sort'] for p in d['parameters']]==[p['sort'] for p in actual['parameters']]
            assert d['result']==actual['result']
            native['declarations'][i]=actual
    return normalize_document(native),slots

def run(group,name,args,model,mode='boundary'):
    old={'frame':frame,'ray':ray,'method':method}[group]
    doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in old.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jsmcpoint',lambda:'discourse')
    mm.setdefault('jsmcprogram',lambda method,stage,seq:seq if (method,stage)==('method','discourse') else SequenceValue((),seq.element_type))
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    h={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=old.DOMAIN,situations=method.POINTS if group=='method' else ('context','other'),
        primitives=h,max_steps=500000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone_models(module,group,names,extra=None):
    """Reuse model bodies with Native values and a decoded-document runner."""
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        pair=pair,symbol=value,run=lambda name,args,m,mode='boundary':run(group,name,args,m,mode))|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

FRAME_CHECKS=('local_checks','scope_checks','segment_checks','physical_checks','pair_checks')
RAY_CHECKS=('origin_checks','path_checks','trace_checks','connection_checks','substitution_checks')
METHOD_CHECKS=('target_checks','chain_checks','premise_checks','presentation_checks')

@lru_cache(None)
def models():
    a=clone_models(frame,'frame',('model','relations',*FRAME_CHECKS))
    b=clone_models(ray,'ray',('model','relations',*RAY_CHECKS),dict(base_model=a['model']))
    c=clone_models(method,'method',METHOD_CHECKS)
    return dict(frame=a,ray=b,method=c)

@pytest.mark.parametrize('group,name', [('frame',n) for n in FRAME_CHECKS]+[('ray',n) for n in RAY_CHECKS]+[('method',n) for n in METHOD_CHECKS])
def test_decoded_native_distinguishing_models(group,name):
    result=models()[group][name]()
    assert result

def test_source_backprojection_and_preserved_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[125,126,127,128]
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(65,69)]
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(118,124)]
    assert [len(s['tokens']) for s in b['text_boundaries']['sentences'].values()]==[44,16]
    assert len(check.NEW_DEFINITIONS)==39 and len(check.vocabulary()._words)==776
    assert doc['statements'][:95]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    ds={d['name']:d for d in check.source_excerpt()['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        assert profile.CONTRACTS[new]['parameters']==ds[old]['parameters']
        assert profile.CONTRACTS[new]['result']==ds[old]['result']

def context(doc):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{
        check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def evaluate(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),
        situations=check.SITUATIONS,primitives=h)]

def description(old):
    return DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),
        check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))

def test_reference_lookup_never_executes_roles():
    for old in (*check.SENTENCES,*check.SPANS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='spatialcapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('spatialcapture',call(check.names()[old])))]
        assert evaluate(doc,context(doc)|dict(spatialcapture=lambda x:x==check.BASE[old]))==[True]

def test_reference_roles_scopes_types_and_unknowns():
    b=check.BASE;h=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        key=[b['eirf'],b[check.reference_anchor(old)],description(old),b['ri']]
        assert h['describedreference'](*key)==b[old]
        for slot in range(4):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['describedreference'](*bad)
        for other in check.ROLE_ASSIGNMENTS:
            if other==old:continue
            # Both ray roles share a node. Selecting the other role returns
            # the other known segment, never an inferred substitute.
            bad=key.copy();bad[2]=description(other)
            if check.reference_anchor(other)==check.reference_anchor(old):assert h['describedreference'](*bad)==b[other]
            else:
                with pytest.raises(ValueError):h['describedreference'](*bad)
        for badrole in (DescriptionValue('{}',key[2].result_type),DescriptionValue(key[2].syntax,'"individual"'),DescriptionValue(key[2].syntax,key[2].result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*key[:2],badrole,key[3])
    for old,(node,first,last) in check.SPANS.items():
        key=[b['eirf'],b[node],first,b[node],last,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencetokenspanreference'](b['eirf'],b['affinetimesentence'],12,b['affinetimesentence'],19,b['ri'])==b['zew']

def test_whole_four_attributions_preserve_order_and_nonfactivity():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][95:99];b=check.BASE
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for node,message in (('ze7','ei5o'),('ze2','ei5q'),('ze3','ei5s'),('ze4','ei5u'))},
          'ue':{(b[first],b[last],b['ri']) for first,last in (('zev','ze7'),('ze7','ze2'),('ze2','ze3'),('ze3','ze4'))}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert evaluate(doc,h)==[True]*4
    for n,rs in rows.items():
        for row in rs:
            result=evaluate(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==3

def role_probe(old,args,model):
    doc=deepcopy(check.restored()['document']);m=mapping();target=check.reference_roles()[old]
    for d in doc['declarations']:
        if d['name'] in {m['ei5a'],m['zlw'],m['rd'],m['zb6']}:
            if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
            d['kind']='primitive';d.pop('body',None)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(target);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    for name,sort in (('probecandidate','individual'),('probecontext','situation')):
        doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=sort))
    doc['statements']=[dict(kind='ask',body=call(target,call('probecandidate'),call('probecontext')))]
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    h|={m[n]:f for n,f in model.items() if m[n] in h}|dict(probecandidate=lambda:args[0],probecontext=lambda:args[1])
    return evaluate_document(doc,individuals=('a','b'),situations=('physical','discourse','other'),primitives=h)[0]['value']

def test_native_reference_roles_bind_each_segment_slot_and_method_stage():
    base=dict(zb6=lambda:'physical',rd=lambda:'b',
        ei5a=lambda rest,moving,ctx:(rest,moving,ctx)==('a','b','physical'),
        zlw=lambda actor,method,stage:(actor,method,stage)==('b','a','discourse'))
    for old,expected in (('zey','b'),('zez','a'),('eisnn','a')):
        assert role_probe(old,[expected,'discourse'],base)
        assert not role_probe(old,['a' if expected=='b' else 'b','discourse'],base)
        boundary='zlw' if old=='eisnn' else 'ei5a'
        with pytest.raises(ValueError,match='Unknown clock-site-time'):
            role_probe(old,[expected,'discourse'],base|{boundary:forbidden})
        for slot in range(3):
            wanted=('b','a','discourse') if old=='eisnn' else ('a','b','physical')
            changed=tuple('other' if i==slot else x for i,x in enumerate(wanted))
            assert not role_probe(old,[expected,'discourse'],base|{boundary:lambda *xs,changed=changed:xs==changed})
    assert not role_probe('eisnn',['a','other'],base)
