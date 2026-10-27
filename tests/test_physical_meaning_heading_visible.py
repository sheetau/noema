"""Run distinguishing models against definitions recovered from visible pages.

The preserved reviewers supply models and abstraction boundaries. Every source
definition under test is replaced by the decoded Native definition. References
and closed roles are checked separately. Motion diagnostics instantiate two real witnesses and vary both, retaining
complete-history argument boundaries and refusal of unbounded real evaluation. These are binding diagnostics, not proofs over the full domain.
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
from scripts import check_einstein_physical_meaning_heading_visible as check
from scripts import physical_meaning_heading_visible_profile as profile
from scripts import check_four_coordinate_claim as four
from scripts import check_physical_meaning_heading as source
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

CHECKS=('motion_checks','subject_checks','presentation_checks')

@lru_cache(None)
def fixture(name,mode='boundary'):
    blueprint,slots=source.fixture(name,mode)
    doc=normalize_document(renamed(deepcopy(blueprint),mapping()))
    decoded={d['name']:d for d in check.restored()['document']['declarations']}
    for i,d in enumerate(doc['declarations']):
        if d['kind']!='definition':continue
        actual=deepcopy(decoded[d['name']])
        if mode=='instance' and d['name']==mapping()[name]:
            assert len(expose(actual,{'exists'},only_sort=RS))==2
        assert [p['sort'] for p in actual['parameters']]==[p['sort'] for p in d['parameters']]
        assert actual['result']==d['result'];doc['declarations'][i]=actual
    return normalize_document(doc),slots


def run(name,args,model,mode='boundary'):
    doc,slots=fixture(name,mode);assert len(args)==len(slots)
    mm={n:lambda x=x:x for n,x in source.CONSTANTS.items()}|model|{n:lambda x=x:x for n,x in zip(slots,args)}
    mapped={mapping().get(n,n):fn for n,fn in mm.items()}
    return evaluate_document(doc,individuals=source.DOMAIN,situations=source.POINTS,
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
    body=clone(segment,('model',));norm=clone(geometry,('norm_factory',),dict(value=value))
    return clone(source,CHECKS,dict(body_model=body['model'],norm_factory=norm['norm_factory'],run=run))


@pytest.mark.parametrize('name',CHECKS)
def test_decoded_native_distinguishing_models(name):assert models()[name]()


def test_source_backprojection_parent_and_public_contract():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    b=check.bridge();assert b['source_statement_indices']==[162]
    assert list(b['source_units'])==['einstein-1905:u0109'] and b['math']==[]
    assert len(doc['declarations'])==2047 and len(doc['statements'])==138
    parent=check.previous.document();assert doc['statements'][:137]==parent['statements']
    ds={d['name']:d for d in doc['declarations']};assert all(ds[d['name']]==d for d in parent['declarations'])
    voc=check.vocabulary().document();old=check.previous.vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):assert all(voc[field].get(n)==d for n,d in old[field].items())
    assert len(check.vocabulary()._words)==802 and len(check.NEW_DEFINITIONS)==6
    assert b['new_public_relations']==1 and b['new_reference_primitives']==0


def test_native_real_witness_body_is_preserved_and_subjects_keep_distinct_motion():
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    native={d['name']:d for d in fixture('ejer')[0]['declarations']}
    assert native[mapping()['ejer']]==ds[mapping()['ejer']]
    def refs(old):return set(_references(ds[mapping()[old]]['body']))
    assert {mapping()[n] for n in ('eigy','eiag')}<=refs('ejes')
    assert mapping()['ejer'] in refs('ejet') and not refs('ejet')&{mapping()[n] for n in ('eigy','eiag')}
    assert {mapping()[n] for n in ('ssn','eiyz','eiy2')}<=refs('ejeu')
    assert not set(check.mapping())&{'sta','stb','zbq','xm','eir3','uh'}


def test_heading_ordinal_division_and_unknown_inputs():
    b=check.BASE;h=check.context_handlers(b)
    assert h['headingreference'](b['ri'],Q(5))==b['zht']
    for args in (('unknown',Q(5)),(b['ri'],Q(0)),(b['ri'],Q(99)),(b['ri'],Q(5,2))):
        with pytest.raises(ValueError):h['headingreference'](*args)
    division=check.text_boundaries()
    assert (division['heading_ordinal'],division['displayed_number'],division['depth'])==(5,4,2)
    assert (division['first_unit'],division['last_unit'],division['next_heading'])==('einstein-1905:u0109','einstein-1905:u0128','einstein-1905:u0129')
    assert division['parent']=='eisdx' and division['section']=='eisn5' and division['heading']=='zht'


def test_native_text_references_do_not_execute_their_claims():
    b=check.BASE
    for old in (*check.HEADINGS,*check.ROLE_ASSIGNMENTS):
        doc=deepcopy(check.restored()['document'])
        doc['declarations'].append(dict(kind='primitive',name='physicalheadingreferencecapture',parameters=['individual'],result='truth'))
        doc['statements']=[dict(kind='ask',body=call('physicalheadingreferencecapture',call(check.names()[old])))]
        handlers={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        handlers.update({check.vocabulary()._symbols[n]:f for n,f in check.context_handlers(b).items()})
        handlers['physicalheadingreferencecapture']=lambda x:x==b[old]
        result=evaluate_document(doc,individuals=tuple(set(b.values())|{'other'}),situations=check.SITUATIONS,primitives=handlers)
        assert [r['value'] for r in result]==[True]


def test_section_reference_arguments_type_rank_and_unknown_rejection():
    b=check.BASE;h=check.context_handlers(b)
    role=DescriptionValue(check.canonical(dict(kind='function_ref',symbol=check.reference_roles()['eisn5'])),check.canonical(dict(kind='function',parameters=['individual','situation'],result='truth')))
    args=[b['eirf'],b['zht'],role,b['ri']]
    assert h['describedreference'](*args)==b['eisn5']
    for slot in range(4):
        bad=args.copy();bad[slot]='unknown'
        with pytest.raises(ValueError):h['describedreference'](*bad)
    for bad in (DescriptionValue('{}',role.result_type),DescriptionValue(role.syntax,'"individual"'),DescriptionValue(role.syntax,role.result_type,1)):
        with pytest.raises(ValueError):h['describedreference'](*args[:2],bad,args[3])


def test_native_section_role_binds_all_hierarchy_arguments():
    ds={d['name']:d for d in check.restored()['document']['declarations']};role=deepcopy(ds[check.reference_roles()['eisn5']]);boundaries=[]
    for name in ('zht','eisdx','eirf','eisdv'):
        d=ds[mapping()[name]];sorts=[p['sort'] for p in d['parameters']] if d['kind']=='definition' else d['parameters']
        boundaries.append(dict(kind='primitive',name=d['name'],parameters=sorts,result=d['result']))
    for name,sort in (('sectioncandidate','individual'),('sectioncontext','situation')):
        boundaries.append(dict(kind='primitive',name=name,parameters=[],result=sort))
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=boundaries+[role],statements=[dict(kind='ask',body=call(role['name'],call('sectioncandidate'),call('sectioncontext')))]))
    row=('heading','section','part','paper',Q(2),Q(4),'discourse')
    base={'sectioncandidate':lambda:'section','sectioncontext':lambda:'discourse',mapping()['zht']:lambda:'heading',mapping()['eisdx']:lambda:'part',mapping()['eirf']:lambda:'paper'}
    def runrole(rows):return evaluate_document(doc,individuals=('heading','section','part','paper','other'),situations=('discourse','other'),primitives=base|{mapping()['eisdv']:relation(rows)})[0]['value']
    assert runrole({row})
    for slot in range(7):assert not runrole({tuple((Q(9) if i in (4,5) else 'wrong') if i==slot else x for i,x in enumerate(row))})
    with pytest.raises(ValueError):evaluate_document(doc,individuals=('heading','section','part','paper','other'),situations=('discourse','other'),primitives=base|{mapping()['eisdv']:forbidden})
