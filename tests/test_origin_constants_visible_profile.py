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
from scripts import check_einstein_origin_constants_visible as check
from scripts import origin_constants_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_origin_constants_claim as source
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

MODULES={'four':four,'origin':source}
CHECKS=('numeric_checks','graph_checks','context_checks','presentation_checks')

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
        if group=='origin' and mode=='instance' and d['name']==mapping()[name]:
            assert expose(actual)=={'ei7n':4,'sqd':2,'smq':1,'smb':3}[name]
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots

def run(group,name,args,model,mode='boundary',domain=None):
    module=MODULES[group];doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in module.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mm.setdefault('jfccpoint' if group=='four' else 'joccpoint',lambda:'discourse')
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    handlers={d['name']:mapped.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'}
    return evaluate_document(doc,individuals=module.DOMAIN if domain is None else domain,
        situations=('context','discourse','other') if group=='four' else source.SITUATIONS,
        primitives=handlers,max_steps=900000,memoize_definitions=True,memoize_expressions=True)[0]['value']

def four_model_fixture(name,mode='boundary'):
    doc,slots=fixture('four',name,mode)
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
    base=clone_models(four,('model','capture','numeric_sequence','matches'),dict(
        run=lambda name,args,m,mode='boundary',domain=None:run('four',name,args,m,mode,domain),
        fixture=four_model_fixture,parse=parse,format_graph=format_graph,evaluate_document=evaluate_document))
    return clone_models(source,('translated','uncertainty_model','captured',*CHECKS),dict(
        previous_model=base['model'],
        run=lambda name,args,m,mode='boundary',domain=None:run('origin',name,args,m,mode,domain)))

@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()

def test_decoded_candidate_family_current_agreement_and_witness():
    ns=models();cuts,m=ns['uncertainty_model']();c=cuts.make;r=cuts.read;count=0
    captured=ns['captured'];SITUATIONS=source.SITUATIONS
    run=lambda name,args,m,mode='boundary',domain=None:globals()['run']('origin',name,args,m,mode,domain)
    family=captured('sqc',m);coefficient=captured('spc',m)
    domain=FunctionValue((RS,),'truth',lambda x:0<=r(x)<5);same=FunctionValue((RS,RS),'truth',lambda a,b:r(a)==r(b))
    alt=FunctionValue(('individual','situation','situation'),'truth',m['zet'])
    for speed in (0,3,4):
        assert run('smq',[coefficient,family,'stage',domain,c(Q(speed))],m,'instance');count+=1
        assert run('smq',[coefficient,family,'other',domain,c(Q(speed))],m,'instance')==(speed==3);count+=1
        assert run('smb',['agent','stage',domain,alt,family,same,'stage','other',c(Q(speed))],m,'instance')==(speed!=3);count+=1
    def fingerprint(f):return tuple(tuple(r(f(ctx)(c(Q(v)))) for v in (0,3,4)) for ctx in SITUATIONS)
    def one(f):return tuple(r(f(c(Q(v)))) for v in (0,3,4))
    def scope(f):return tuple(f(c(Q(v))) for v in (-3,0,3,4,5))
    expected_family=fingerprint(family);expected_current=one(coefficient)
    m|={'smq':lambda f,fam,stage,dom:one(f)==expected_current and fingerprint(fam)==expected_family and stage=='stage' and scope(dom)==(False,True,True,True,False),
        'smb':lambda agent,stage,dom,alternatives,fam,same:agent=='agent' and stage=='stage' and scope(dom)==(False,True,True,True,False) and alternatives(agent,stage,'stage') and alternatives(agent,stage,'other') and fingerprint(fam)==expected_family and same(c(Q(2)),c(Q(2))) and not same(c(Q(2)),c(Q(3)))}
    for ctx in SITUATIONS:
        assert run('sqd',[ctx,c(Q(3))],m,'instance');count+=1
    for symbol in ('smq','smb'):
        assert not run('sqd',['other',c(Q(3))],m|{symbol:lambda *xs:False},'instance');count+=1
    assert not run('sqd',['other',c(Q(3))],m|{'zet':lambda a,s,t:t=='other'},'instance');count+=1
    assert not run('sqd',['other',c(Q(3))],m|{'zfm':lambda:'context'},'instance')
    unknowns(lambda mm:run('sqd',['other',c(Q(3))],mm,'instance'),m,('zer','zet','zeq','smq','smb','tc','sky'))
    try:run('sqd',[],m)
    except ValueError as error:assert 'Cannot finitely quantify' in str(error)
    else:raise AssertionError('Whole candidate functions sampled')

def test_source_backprojection_and_complete_unit_boundaries():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[138,139]
    assert list(b['source_units'])==['einstein-1905:u0085']
    assert [r['id'] for r in b['math']]==['M0137','M0138','M0139']
    text=b['text_boundaries'];assert text['spans']=={'zfp':['fourcoordinatesentence',14,22],'zfq':['originconstantssentence',1,29]}
    assert text['sentences']['fourcoordinatesentence']==check.previous.text_boundaries()['sentences']['fourcoordinatesentence']
    assert len(text['sentences']['originconstantssentence']['tokens'])==29
    assert len(check.NEW_DEFINITIONS)==13 and len(check.vocabulary()._words)==782
    assert doc['statements'][:108]==check.previous.document()['statements']
    prior=check.previous.vocabulary().document();current=check.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):
        assert all(current[field][n]==d for n,d in prior[field].items())
    assert len(profile.CONTRACTS)==2 and b['forwarded_reference_signatures']=={}
    assert not {'sqe','sqf'}&set(check.mapping())

def test_stage_reference_is_distinct_scoped_and_opaque():
    b=check.BASE;handlers=check.context_handlers(b)
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['zfm'])),
        check.canonical(dict(kind='function',parameters=['situation','situation'],result='truth')))
    args=[b['eirf'],b['zfp'],role,b['ri']]
    assert handlers['describedsettingreference'](*args)==b['zfm']!=b['zes']
    for slot in range(4):
        bad=args.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):handlers['describedsettingreference'](*bad)
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):handlers['describedsettingreference'](*args[:2],bad,args[3])
    doc=deepcopy(check.restored()['document'])
    doc['declarations'].append(dict(kind='primitive',name='origincapture',parameters=['situation'],result='truth'))
    doc['statements']=[dict(kind='ask',body=call('origincapture',call(check.names()['zfm'])))]
    h={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    h|={check.vocabulary()._symbols[n]:f for n,f in handlers.items()}
    h['origincapture']=lambda x:x==b['zfm']
    assert evaluate_document(doc,individuals=tuple(set(b.values())|{'other','setting','frame'}),situations=check.SITUATIONS,primitives=h)[0]['value']

def test_inherited_and_new_token_spans_share_sentence_without_shadowing():
    b=check.BASE;h=check.context_handlers(b)
    expected={'zfj':('fourcoordinatesentence',1,11),'zfk':('fourcoordinatesentence',12,13),**check.SPANS}
    for old,(node,start,end) in expected.items():
        assert h['sentencetokenspanreference'](b['eirf'],b[node],Q(start),b[node],Q(end),b['ri'])==b[old]
    for args in ((b['eirf'],b['fourcoordinatesentence'],Q(13),b['fourcoordinatesentence'],Q(22),b['ri']),
                 (b['eirf'],b['originconstantssentence'],Q(1),b['originconstantssentence'],Q(30),b['ri'])):
        with pytest.raises(ValueError):h['sentencetokenspanreference'](*args)
