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
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,SequenceValue,DescriptionValue,evaluate_document
from scripts import check_einstein_four_coordinate_visible as check
from scripts import four_coordinate_visible_profile as profile
from scripts import check_four_coordinate_claim as source
from scripts import check_spatial_affine_calibration as calibration
from scripts import check_transverse_ray_claim as rays
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

MODULES={'calibration':calibration,'source':source}
CHECKS={'calibration':('row_checks','correspondence_checks','origin_checks','calibration_checks','connection_checks'),
        'source':('numeric_checks','system_checks','graph_checks','presentation_checks')}

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
def fixture(group,name,mode='boundary'):
    blueprint,slots=MODULES[group].fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if group=='calibration' and mode=='instance' and d['name']==mapping()[name]:
            assert expose(actual)=={'smd':4,'ei6z':2,'ei66':3}[name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run_fixture(group,doc,slots,args,model,domain=None):
    module=MODULES[group];assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in module.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jsacpoint' if group=='calibration' else 'jfccpoint',lambda:'context' if group=='calibration' else 'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    h={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=module.DOMAIN if domain is None else domain,
        situations=('context','other') if group=='calibration' else ('context','discourse','other'),
        primitives=h,max_steps=700000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def run(group,name,args,model,mode='boundary',domain=None):
    doc,slots=fixture(group,name,mode);return run_fixture(group,doc,slots,args,model,domain)

def source_model_fixture(name,mode='boundary'):
    # The preserved coefficient-mutation diagnostic evaluates a fixture directly.
    # Supply decoded Native bodies in its old label namespace, with Native values.
    doc,slots=fixture('source',name,mode)
    return normalize_document(renamed(deepcopy(doc),{v:k for k,v in mapping().items()})),slots

def clone_models(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation,
        symbol=value)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models():
    base=clone_models(rays,('model',))
    result={}
    for group,module in MODULES.items():
        extra=dict(run=lambda name,args,m,mode='boundary',domain=None,group=group:run(group,name,args,m,mode,domain))
        if group=='calibration':extra['transverse_model']=base['model'];helpers=()
        else:
            helpers=('capture','numeric_sequence','matches')
            extra|=dict(fixture=source_model_fixture,parse=parse,format_graph=format_graph,evaluate_document=evaluate_document)
        result[group]=clone_models(module,('model',*helpers,*CHECKS[group]),extra)
    return result

@pytest.mark.parametrize('group,name',[(g,n) for g,checks in CHECKS.items() for n in checks])
def test_decoded_native_distinguishing_models(group,name):assert models()[group][name]()

def test_source_backprojection_boundaries_and_preserved_contracts():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[136,137]
    assert list(b['source_units'])==['einstein-1905:u'+str(i).zfill(4) for i in range(81,85)]
    assert [r['id'] for r in b['math']]==['M0134','M0135','M0136']
    boundary=b['text_boundaries'];sentence=boundary['sentences']['fourcoordinatesentence']
    assert len(sentence['tokens'])==22 and sentence['tokens'][13:]==['und','[M0137]','eine','vorläufig','unbekannte','Funktion','von','[M0138]','ist.']
    assert boundary['sentence_context_only']['range']==[0,63] and not boundary['sentence_context_only']['assertions_integrated_here']
    assert b['sentence_coordinates']=={'fourcoordinatesentence':[43,1]}
    assert len(check.NEW_DEFINITIONS)==31 and len(check.vocabulary()._words)==780
    assert doc['statements'][:106]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(profile.CONTRACTS)==len(profile.EXTRA)==1
    assert b['forwarded_reference_signatures']['zfh']['parameters']==['individual']
    assert b['forwarded_reference_signatures']['zfh']['result']==profile.TAU

def context(doc,values=None):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{
        check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE if values is None else values).items()}

def evaluate(doc,h):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),
        situations=check.SITUATIONS,primitives=h)]

def description(old):
    sort=profile.ROLE if old=='coordinatespatialfamily' else dict(kind='function',parameters=['individual','situation'],result='truth')
    return DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(sort))

def family(table):
    def get(axis):
        if axis not in table:forbidden()
        return table[axis]
    return FunctionValue(('individual',),profile.TAU,get)

def test_reference_types_scopes_unknowns_and_nonexecution():
    b=check.BASE;opaque=FunctionValue(('individual',),profile.TAU,forbidden)
    values=b|dict(coordinatespatialfamily=opaque);h=check.context_handlers(values)
    for old,handler,result in (('coordinatespatialfamily','describedindividualfourcutfunctionfamilyreference',opaque),('zfi','describedreference',b['zfi'])):
        key=[b['eirf'],b['zfj'],description(old),b['ri']];assert h[handler](*key)==result
        for slot in range(4):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h[handler](*bad)
        for bad in (DescriptionValue('{}',key[2].result_type),DescriptionValue(key[2].syntax,'"individual"'),DescriptionValue(key[2].syntax,key[2].result_type,1)):
            with pytest.raises(ValueError):h[handler](*key[:2],bad,key[3])
        doc=deepcopy(check.restored()['document']);sort=profile.MAP if old=='coordinatespatialfamily' else 'individual'
        doc['declarations'].append(dict(kind='primitive',name='fourcapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('fourcapture',call(check.names()[old])))]
        assert evaluate(doc,context(doc,values)|dict(fourcapture=lambda x:True))==[True]
    for invalid in ('not a function',FunctionValue(('number',),profile.TAU,forbidden),FunctionValue(('individual',),'individual',forbidden),FunctionValue(('individual',),profile.TAU,None)):
        with pytest.raises(ValueError):profile.IndividualFourCutFamilyReferences({('d','n','role','s'):invalid})

def test_native_family_forwarding_preserves_each_axis_without_evaluating_member():
    b=check.BASE;cuts=Cuts();members={b[a]:FunctionValue(tuple(profile.TAU['parameters']),RS,forbidden) for a in ('yn','yo','yp')}
    seen=[]
    def lookup(axis):
        seen.append(axis)
        if axis not in members:forbidden()
        return members[axis]
    values=b|dict(coordinatespatialfamily=FunctionValue(('individual',),profile.TAU,lookup))
    doc=deepcopy(check.restored()['document'])
    doc['declarations'] += [dict(kind='primitive',name='fourprobeaxis',parameters=[],result='individual'),dict(kind='primitive',name='fourcapture',parameters=[profile.TAU],result='truth')]
    doc['statements']=[dict(kind='ask',body=call('fourcapture',call(check.names()['zfh'],call('fourprobeaxis'))))]
    for axis in ('yn','yo','yp'):
        seen.clear();h=context(doc,values)|dict(fourprobeaxis=lambda axis=axis:b[axis],fourcapture=lambda fn:fn.parameters==tuple(profile.TAU['parameters']) and fn.result==RS)
        assert evaluate(doc,h)==[True] and seen==[b[axis]]
        with pytest.raises(ValueError,match='Unknown clock-site-time'):evaluate(doc,h|dict(fourprobeaxis=lambda:'other'))

def test_sentence_spans_and_continuation_not_truncated_at_beta():
    b=check.BASE;h=check.context_handlers(b)
    assert h['sentencereference'](b['ri'],43,1)==b['fourcoordinatesentence']
    for old,(node,start,end) in check.SPANS.items():
        key=[b['eirf'],b[node],start,b[node],end,b['ri']]
        assert h['sentencetokenspanreference'](*key)==b[old]
        for slot in range(6):
            bad=key.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['sentencetokenspanreference'](*bad)
    assert h['sentencereference'](b['ri'],42,1)==b['transverseraysentence']
    for n in (0,23,Q(3,2)):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](b['eirf'],b['fourcoordinatesentence'],1,b['fourcoordinatesentence'],n,b['ri'])

def test_whole_annotation_remains_outside_two_author_attributions():
    b=check.BASE;doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][106:108]
    rows={'eir3':{(b[node],b['rd'],b['eirf'],message,b['ri']) for _,message,_,node,_ in source.GROUPS},
          'ue':{(b[prior],b[node],b['ri']) for _,_,_,node,prior in source.GROUPS},
          'zfl':{(b['zfi'],b['rd'],'ei66','ei7b',b['eisms'],b['ri'])}}
    h=context(doc)|{mapping()[n]:relation(rs) for n,rs in rows.items()}
    assert evaluate(doc,h)==[True,True]
    for n,rs in rows.items():
        for row in rs:
            result=evaluate(doc,h|{mapping()[n]:relation(rs-{row})})
            assert result.count(False)==1 and result.count(True)==1
    assert evaluate(doc,h|{mapping()['zfl']:relation(set())})==[False,True]

def test_native_annotation_role_keeps_all_six_slots():
    b=check.BASE;doc=deepcopy(check.restored()['document'])
    doc['statements']=[dict(kind='ask',body=call(check.reference_roles()['zfi'],call(check.names()['zfi']),call(check.names()['ri'])))]
    row=(b['zfi'],b['rd'],'ei66','ei7b',b['eisms'],b['ri']);target=mapping()['zfl'];h=context(doc)|{target:relation({row})}
    assert evaluate(doc,h)==[True]
    for slot in range(6):
        changed=tuple('other' if i==slot else x for i,x in enumerate(row))
        assert evaluate(doc,h|{target:relation({changed})})==[False]
    with pytest.raises(ValueError,match='Unknown clock-site-time'):evaluate(doc,h|{target:forbidden})

def test_native_family_forwarding_joins_same_calibration_body():
    cuts,m,rows,norm,records,coords,mat,off,matrix,offset,functions,affine,tracks=models()['calibration']['model']()
    doc,slots=fixture('calibration','ei65','integrated');doc=deepcopy(doc)
    actual={d['name']:d for d in check.restored()['document']['declarations']}
    target=mapping()['zfh'];doc['declarations']=[deepcopy(actual[target]) if d['name']==target else d for d in doc['declarations']]
    # The family must be declared before the forwarded definition uses it.
    doc['declarations'].insert(0,dict(kind='primitive',name=check.names()['coordinatespatialfamily'],parameters=[],result=profile.MAP))
    def probe(candidate):
        return run_fixture('calibration',doc,slots,[matrix,offset,'o1'],m|{'coordinatespatialfamily':lambda:candidate})
    assert probe(family(functions))
    for axis in ('x','y','z'):
        wrong='y' if axis=='x' else 'x';assert not probe(family(functions|{axis:functions[wrong]}))

@lru_cache(None)
def family_role_fixture(instance):
    doc=deepcopy(check.restored()['document']);m=mapping();target=check.reference_roles()['coordinatespatialfamily']
    for d in doc['declarations']:
        if d['name'] in {m['ei6z'],m['yn'],m['yo'],m['yp']}:
            if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
            d['kind']='primitive';d.pop('body',None)
        if d['name']==target and instance:assert expose(d)==2
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(target);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    sorts=[profile.MAP,'situation']+([profile.MATRIX,profile.VECTOR] if instance else [])
    names=['fourrolecandidate','fourrolecontext','fourrolematrix','fourroleoffset'][:len(sorts)]
    doc['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=s) for n,s in zip(names,sorts)]
    doc['statements']=[dict(kind='ask',body=call(target,*(call(n) for n in names)))]
    return doc,names

def test_common_matrix_and_offset_role_bindings_and_full_domain_refusal():
    cuts=Cuts();c=cuts.make;r=cuts.read;m=mapping()
    members={a:FunctionValue(tuple(profile.TAU['parameters']),RS,lambda *xs,i=i:c(i)) for i,a in enumerate(('x','y','z'))}
    candidate=family(members)
    matrix=lambda n:FunctionValue(('individual','individual'),RS,lambda a,b:c(n))
    offset=lambda n:FunctionValue(('individual',),RS,lambda a:c(n))
    rows={(i,a,Q(10),Q(20)) for i,a in enumerate(('x','y','z'))}
    def norm(fn,axis,mat,off):return (r(fn(*[c(0)]*4)),axis,r(mat('x','x')),r(off('x')))
    def probe(args,rows=rows,instance=True):
        doc,names=family_role_fixture(instance)
        h={m['yn']:lambda:'x',m['yo']:lambda:'y',m['yp']:lambda:'z',m['ei6z']:lambda *xs:norm(*xs) in rows}
        h|={n:lambda x=x:x for n,x in zip(names,args)}
        return evaluate_document(doc,individuals=('x','y','z'),situations=('discourse','other'),primitives=h)[0]['value']
    args=[candidate,'discourse',matrix(10),offset(20)];assert probe(args)
    for slot,replacement in ((2,matrix(11)),(3,offset(21))):
        changed=args.copy();changed[slot]=replacement;assert not probe(changed)
    for row in rows:
        assert not probe(args,rows-{row})
        for slot in (0,1):
            changed=tuple(('other' if slot==1 else Q(99)) if i==slot else x for i,x in enumerate(row))
            assert not probe(args,(rows-{row})|{changed})
    with pytest.raises(ValueError,match='Cannot finitely quantify'):probe(args[:2],instance=False)
