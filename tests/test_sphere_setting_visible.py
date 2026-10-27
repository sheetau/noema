"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Real witnesses are instantiated only in diagnostics, preserving the original
Native bodies, full history boundaries and refusal of unbounded real evaluation. These are binding diagnostics, not proofs over the full domain.
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
from scripts import check_einstein_sphere_setting_visible as check
from scripts import physical_meaning_heading_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_sphere_setting as source
from scripts import check_solid_sphere_geometry as solid
from scripts import check_transverse_segment as segment
from scripts import check_moving_trip_geometry as geometry
from scripts.check_translated_light_trial import expose
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

SOLID_CHECKS=('geometry_checks','history_checks','record_checks','coverage_checks','setting_checks')
SOURCE_CHECKS=('surface_checks','content_checks','presentation_checks')


@lru_cache(None)
def fixture(group,name,mode='boundary'):
    module=solid if group=='solid' else source
    blueprint,slots=module.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            count=len(expose(actual,{'forall','exists'},only_sort=RS))
            assert count==({'eje3':4,'eje4':3,'eje5':1,'eje7':1}[name] if group=='solid' else 3)
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(group,name,args,model,mode='boundary',domain=None):
    module=solid if group=='solid' else source
    doc,slots=fixture(group,name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in module.CONSTANTS.items()}|{'jsstpoint':lambda:'discourse'}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=module.DOMAIN if domain is None else domain,situations=('context','discourse','other'),
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
def models(group):
    body=clone(segment,('model',));module=solid if group=='solid' else source
    def wrapped(name,args,model,mode='boundary',domain=None):return run(group,name,args,model,mode,domain)
    return clone(module,SOLID_CHECKS if group=='solid' else SOURCE_CHECKS,dict(body_model=body['model'],run=wrapped))


@pytest.mark.parametrize('name',SOLID_CHECKS)
def test_decoded_solid_geometry_and_full_record_bindings(name):assert models('solid')[name]()


@pytest.mark.parametrize('name',SOURCE_CHECKS)
def test_decoded_setting_surface_and_author_note(name):assert models('source')[name]()


def test_source_backprojection_parent_and_unchanged_vocabulary():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[163,164,165]
    assert list(b['source_units'])==['einstein-1905:u0110','einstein-1905:u0111','einstein-1905:u0281']
    assert [r['id'] for r in b['math']]==['M0191','M0192','M0193','M0194','M0195','M0196']
    assert len(doc['declarations'])==2084 and len(doc['statements'])==141
    parent=check.previous.document();assert doc['statements'][:138]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    assert check.vocabulary().document()==check.previous.vocabulary().document()
    assert len(check.vocabulary()._words)==802 and len(check.NEW_DEFINITIONS)==28
    assert b['new_public_relations']==b['new_reference_primitives']==0


def test_native_bodies_keep_real_quantifiers_and_independent_boundary():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    for group,names in (('solid',('eje3','eje4','eje5','eje7')),('source',('ejfe',))):
        for name in names:
            native={d['name']:d for d in fixture(group,name)[0]['declarations']}
            assert native[mapping()[name]]==ds[mapping()[name]]
    def refs(old):return set(_references(ds[mapping()[old]]['body']))
    assert mapping()['eje2'] in refs('eje3') and mapping()['ssz'] not in refs('eje3')
    assert {mapping()[n] for n in ('eiyx','ejfa','ssz')}<=refs('ejfd')
    assert {mapping()[n] for n in ('eje4','eigy','eiah')}<=refs('eje5')
    assert mapping()['eje5'] in refs('ejfe') and mapping()['ejfb'] not in refs('ejfe')
    assert not set(check.mapping())&{'shd','stk','stl','zhu','zhv','eipc','eipe','stf'}


def test_sentence_span_and_footnote_coordinates_reject_each_unknown():
    b=check.BASE;h=check.context_handlers(b)
    for old,pos in check.SENTENCES.items():assert h['sentencereference'](b['ri'],*map(Q,pos))==b[old]
    for args in (('unknown',Q(54),Q(1)),(b['ri'],Q(0),Q(1)),(b['ri'],Q(54),Q(3))):
        with pytest.raises(ValueError):h['sentencereference'](*args)
    cases=[('sentencetokenspanreference',[b['eirf'],b['sphereequationsentence'],Q(16),b['sphereequationsentence'],Q(17),b['ri']],'eisn6'),
           ('footnoteattachmentreference',[b['eirf'],b['zhy'],Q(1),Q(1),b['ri']],'eisoa'),
           ('footnotereference',[b['eirf'],b['eisoa'],Q(1),b['ri']],'eisn7')]
    for name,args,old in cases:
        assert h[name](*args)==b[old]
        for slot in range(len(args)):
            bad=args.copy();bad[slot]=Q(99) if isinstance(args[slot],Q) else 'unknown'
            with pytest.raises(ValueError):h[name](*bad)
    bounds=check.text_boundaries()
    assert [len(row['tokens']) for row in bounds['sentences'].values()]==[23,17]
    assert bounds['sentences']['zhy']['tokens'][4:6]==['Kugel','vom']
    assert bounds['attachment']['after_token']==5 and bounds['attachment']['printed_number']==1
    assert (bounds['footnote']['unit'],bounds['footnote']['original_page'],bounds['footnote']['inventory_page_at_end'])==('einstein-1905:u0281','903','921')
    assert bounds['footnote']['text']=='Das heißt einen Körper, welcher ruhend untersucht Kugelgestalt besitzt.'


def test_native_references_do_not_execute_setting_or_quotes():
    cuts=Cuts();radius=cuts.make(2);b=check.BASE|{'zhx':radius}
    for old in (*check.SENTENCES,*check.SPANS,'eisoa','eisn7',*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document']);sort=RS if old=='zhx' else 'individual'
        doc['declarations'].append(dict(kind='primitive',name='spherereferencecapture',parameters=[sort],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('spherereferencecapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
        handlers['spherereferencecapture']=(lambda x:cuts.read(x)==2) if old=='zhx' else (lambda x:x==b[old])
        result=evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
        assert [r['value'] for r in result]==[True]


def test_body_and_radius_reference_types_rank_and_every_input():
    cuts=Cuts();radius=cuts.make(2);b=check.BASE|{'zhx':radius};h=check.context_handlers(b)
    for old in check.ROLE_ASSIGNMENTS:
        sort=RS if old=='zhx' else 'individual';name='describedcutreference' if old=='zhx' else 'describedreference'
        role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.canonical(dict(kind='function',parameters=[sort,'situation'],result='truth')))
        args=[b['eirf'],b['zhy'],role,b['ri']];found=h[name](*args)
        assert (cuts.read(found)==2) if old=='zhx' else (found==b[old])
        for slot in range(4):
            bad=args.copy();bad[slot]='unknown'
            with pytest.raises(ValueError):h[name](*bad)
        for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
            with pytest.raises(ValueError):h[name](*args[:2],bad,args[3])


def role_fixture(old,boundaries):
    ds={d['name']:d for d in check.restored()['document']['declarations']};role=deepcopy(ds[check.reference_roles()[old]]);decls=[]
    for name in boundaries:
        d=ds[mapping()[name]];sorts=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
        decls.append(dict(kind='primitive',name=d['name'],parameters=sorts,result=d['result']))
    decls+=[dict(kind='primitive',name='spherecandidate',parameters=[],result=RS if old=='zhx' else 'individual'),dict(kind='primitive',name='spherecontext',parameters=[],result='situation')]
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=decls+[role],statements=[dict(kind='ask',body=call(role['name'],call('spherecandidate'),call('spherecontext')))]))


def test_native_body_role_binds_same_radius_and_physical_setting():
    cuts=Cuts();radius=cuts.make(2);doc=role_fixture('zhw',('ejfc','zhx','zb6'))
    row=('body',Q(2),'setting');base={'spherecandidate':lambda:'body','spherecontext':lambda:'discourse',mapping()['zhx']:lambda:radius,mapping()['zb6']:lambda:'setting'}
    def test(rows):
        return evaluate_document(doc,individuals=('body','other'),situations=('setting','discourse','other'),primitives=base|{mapping()['ejfc']:lambda b,r,s:(b,cuts.read(r),s) in rows})[0]['value']
    assert test({row})
    for slot in range(3):assert not test({tuple((Q(3) if i==1 else 'wrong') if i==slot else x for i,x in enumerate(row))})
    with pytest.raises(ValueError):evaluate_document(doc,individuals=('body','other'),situations=('setting','discourse'),primitives=base|{mapping()['ejfc']:forbidden})


def test_native_radius_role_preserves_positivity_and_is_acyclic():
    doc=role_fixture('zhx',('sbg',));cuts=Cuts()
    for number in (-1,0,2):
        result=evaluate_document(doc,individuals=('other',),situations=('discourse',),primitives={'spherecandidate':lambda:cuts.make(number),'spherecontext':lambda:'discourse',mapping()['sbg']:lambda r:cuts.read(r)>0})[0]['value']
        assert result==(number>0)
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    role=ds[check.reference_roles()['zhx']]
    assert not set(_references(role['body']))&{mapping()['zhw'],mapping()['zhx']}
