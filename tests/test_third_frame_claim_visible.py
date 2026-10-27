"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Record diagnostics use two target
events/records and three distinct frame individuals, preserving nonempty domains
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
from scripts import check_einstein_third_frame_claim_visible as check
from scripts import third_frame_claim_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_third_frame_claim as claim
from scripts import check_third_frame_geometry as geometry
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

CHECKS=(('geometry','numeric_checks'),('geometry','geometry_checks'),('geometry','scope_checks'),
        ('claim','rule_checks'),('claim','purpose_checks'),('claim','presentation_checks'))

@lru_cache(None)
def fixture(group,name):
    source=geometry if group=='geometry' else claim
    blueprint,slots=source.fixture(name)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(group,name,args,model,domain=None):
    source=geometry if group=='geometry' else claim
    doc,slots=fixture(group,name);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}|{('jtfgpoint' if group=='geometry' else 'jtfcpoint'):lambda:'discourse'}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN if domain is None else domain,situations=source.POINTS,
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=1200000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def clone(module,names,extra=None):
    ns=dict(vars(module))|dict(FunctionValue=FunctionValue,Content=Content,SequenceValue=SequenceValue,
        numbers=numbers,forbidden=forbidden,unknowns=unknowns,perturb=perturb,relation=relation)|(extra or {})
    for name in names:
        original=getattr(module,name);original=getattr(original,'__wrapped__',original)
        ns[name]=FunctionType(original.__code__,ns,name,original.__defaults__,original.__closure__)
    return ns

@lru_cache(None)
def models(group):
    base=clone(four,('model',));source=geometry if group=='geometry' else claim
    execute=lambda name,args,m,*domain:run(group,name,args,m,domain[0] if domain else None)
    return clone(source,tuple(n for g,n in CHECKS if g==group),dict(previous_model=base['model'],run=execute))

@pytest.mark.parametrize('group,name',CHECKS)
def test_decoded_native_distinguishing_models(group,name):assert models(group)[name]()

def test_all_three_records_same_event_nonempty_scope_and_value_aliases():
    rows={'zc4':{('event',)},'eiyx':{('event','x','K','context'),('event','y','k','context'),('event','z','third','context')}}
    model={n:relation(rs) for n,rs in rows.items()}
    assert perturb(lambda m:run('geometry','eja4',['event','x','y','z','context'],m),model,rows)
    for frame in ('K','k'):
        assert not run('geometry','eja4',['event','x','y','z','context'],model|{'zgi':lambda frame=frame:frame})
    # Two target events/records plus the three frame individuals required by typing.
    small=('a','b');tuples={(e,t,f,'context') for e in small for f in ('K','k','third') for t in (small if f=='third' else ('a',))}
    model={'zc4':lambda e:e in small,'eiyx':lambda *xs:xs in tuples,'shh':lambda a,b:True}
    execute=lambda m:run('geometry','eja5',['context'],m,small+('K','k','third'))
    assert execute(model)
    for event in small:
        for frame in ('K','k','third'):
            assert not execute(model|{'eiyx':lambda e,t,f,s,e0=event,f0=frame:(e,t,f,s) in tuples and (e,f)!=(e0,f0)})
    assert not execute(model|{'zc4':lambda e:False})
    assert not execute(model|{'shh':lambda a,b:a==b})
    unknowns(execute,model,('zc4','eiyx','shh'))

def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)

@lru_cache(None)
def native_fixture(name,bounds=()):
    doc=deepcopy(check.restored()['document']);m=mapping()
    selected={m[n] for n in bounds}
    for d in doc['declarations']:
        if d['name'] in selected:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(n):
        if n in seen:return
        seen.add(n)
        for ref in _references(ds[n].get('body')):visit(ref)
    visit(m[name]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen]
    slots=[]
    for i,p in enumerate(ds[m[name]]['parameters']):
        n='thirdprobe'+chr(97+i);slots.append(n)
        doc['declarations'].append(dict(kind='primitive',name=n,parameters=[],result=p['sort']))
    doc['statements']=[dict(kind='ask',body=call(m[name],*[call(n) for n in slots]))]
    return normalize_document(doc),slots

def native_run(name,args,model,bounds=()):
    doc,slots=native_fixture(name,tuple(bounds));assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in (geometry.CONSTANTS|claim.CONSTANTS).items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    individuals=tuple(dict.fromkeys((*geometry.DOMAIN,*claim.DOMAIN,'a','b','Korigin','korigin','Kx','Ky','Kz','kx','ky','kz')))
    return evaluate_document(doc,individuals=individuals,situations=('context','discourse','other'),
        primitives={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=50000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def test_native_material_axes_and_correspondence_keep_every_contract_slot():
    frames=('K','k');axes=('x','y','z')
    line=lambda f,a:f+a;origin=lambda f:f+'origin'
    rows={
        'va':{(f,) for f in frames},
        'zbv':{(f,origin(f),'context') for f in frames},
        'zbw':{(f,line(f,a),a,'context') for f in frames for a in axes},
        'zbp':{(line(f,a),) for f in frames for a in axes},
        'zbq':{(line(f,a),'context') for f in frames for a in axes},
        'zbr':{(line(f,a),origin(f),'context') for f in frames for a in axes},
        'zbs':{(line(f,a),line(f,b),'context') for f in frames for a,b in (('x','y'),('x','z'),('y','z'))},
        'zbu':{('Kx','kx','context')},
        'zbt':{('Ky','ky','context'),('Kz','kz','context')}}
    model={n:relation(rs) for n,rs in rows.items()}|{
        'zbn':lambda f,s:origin(f) if f in frames and s=='context' else forbidden(),
        'zbo':lambda f,a,s:line(f,a) if f in frames and a in axes and s=='context' else forbidden()}
    # Axis designations are reference inputs; keep sfc and its geometry bodies Native.
    bounds=('yn','yo','yp')
    execute=lambda m:native_run('sfc',['K','k','context'],m,bounds)
    assert perturb(execute,model,rows)
    assert not native_run('sfc',['K','K','context'],model,bounds)
    unknowns(execute,model,('zbn','zbo'))

def test_complete_source_backprojection_and_parent_preservation():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[146,147]
    assert list(b['source_units'])==['einstein-1905:u0093','einstein-1905:u0094']
    assert [r['id'] for r in b['math']]==['M'+str(i).zfill(4) for i in range(150,162)]
    assert len(doc['declarations'])==1896 and len(doc['statements'])==123
    parent=check.previous.document();assert doc['statements'][:116]==parent['statements']
    ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in parent['declarations'])
    assert len(check.NEW_DEFINITIONS)==29 and b['reference_anchors']=={'zgi':'zgo','zgk':'thirdframezero'}

def test_public_contracts_and_previous_profile_preserved():
    voc=check.vocabulary();assert len(voc._words)==796
    before=check.previous.vocabulary().document();after=voc.document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(after[field][n]==d for n,d in before[field].items())
    assert len(profile.SOURCE_RELATIONS)==7
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for old,new in profile.SOURCE_RELATIONS.items():
        source=next(d for d in check.source_excerpt()['declarations'] if d['name']==old)
        actual=ds[mapping()[old]];contract=profile.CONTRACTS[new]
        assert actual['kind']=='primitive' and actual['parameters']==source['parameters']==contract['parameters']
        assert actual['result']==source['result']=='truth'

def context(doc):
    return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}|{check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(check.BASE).items()}

def evaluate(doc,handlers):
    return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=handlers)]

def test_reference_scope_types_unknown_inputs_and_native_nonexecution():
    b=check.BASE;h=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
        args=[b['eirf'],b[check.reference_anchor(old)],role,b['ri']]
        assert h['describedreference'](*args)==b[old]
        for slot in range(4):
            bad=args.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h['describedreference'](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='thirdreferencecapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('thirdreferencecapture',call(check.names()[old])))]
        assert evaluate(doc,context(doc)|dict(thirdreferencecapture=lambda x:x==b[old]))==[True]

def test_native_closed_roles_preserve_frame_identity_and_fixed_zero_setting():
    rows={'va':{('third',)},'eisd3':{('intro','third','paper','discourse')}}
    model={n:relation(rs) for n,rs in rows.items()}
    execute=lambda m:native_run('thirdframerole',['third','discourse'],m,('ra','zbm','zgo','eirf'))
    assert perturb(execute,model,rows)
    for frame in ('K','k'):
        assert not native_run('thirdframerole',[frame,'discourse'],model,('ra','zbm','zgo','eirf'))
    model={'eja3':lambda event,setting:(event,setting)==('zero','context')}
    assert native_run('thirdframezerorole',['zero','discourse'],model,('eja3','zb6'))
    assert not native_run('thirdframezerorole',['other','discourse'],model,('eja3','zb6'))
    assert not native_run('thirdframezerorole',['zero','discourse'],model|{'zb6':lambda:'other'},('eja3','zb6'))
    # Presentation context does not replace the fixed physical setting in this role.
    assert native_run('thirdframezerorole',['zero','other'],model,('eja3','zb6'))

def test_sentence_span_designations_and_all_coordinate_arguments():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():
        assert h['sentencereference'](b['ri'],*map(Q,pos))==b[old]
    for args in ((b['ri'],Q(49),Q(4)),('unknown',Q(49),Q(1)),(b['ri'],Q(0),Q(1))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    args=[b['eirf'],b['thirdframeintroduction'],b['thirdframezero'],b['ri']]
    assert h['sentencespanreference'](*args)==b['zgo']
    for slot in range(4):
        bad=args.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['sentencespanreference'](*bad)
    for old,(node,index) in check.DESIGNATIONS.items():
        args=[b['eirf'],b[node],Q(index),b['ri']]
        assert h['designationreference'](*args)==b[old]
        for slot in range(4):
            bad=args.copy();bad[slot]=Q(99) if slot==2 else 'unknown'
            with pytest.raises(ValueError):h['designationreference'](*bad)
    bnd=check.text_boundaries()
    assert [len(row['tokens']) for row in bnd['sentences'].values()]==[36,21,17]
    assert bnd['sentences']['zgp']['tokens'][-1]=='[M0161]'
    doc=check.restored()['document'];assert len(doc['statements'][118:])==5
    for statement,(old,text) in zip(doc['statements'][118:],check.FORMS.items(),strict=True):
        assert statement==dict(kind='assert',body=call(check.vocabulary()._symbols['printedform'],call(check.names()[old]),check.author.text_expression('de'),check.author.text_expression(text),call(check.names()['ri'])))
