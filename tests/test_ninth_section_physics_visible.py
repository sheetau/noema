"""Check actual decoded bodies before finite point/binder diagnostics.

Point and coefficient-domain substitution is explicit. Finite diagnostics
do not constitute proofs over all real numbers or function spaces.
"""
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
from types import FunctionType
import json
import pytest
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import Content,FunctionValue,DescriptionValue,SequenceValue,QuestionValue,evaluate_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import call,renamed
from scripts import check_einstein_ninth_section_visible as check
from scripts import ninth_section_visible_profile as profile


from scripts.check_tau_differential import ConstructedCuts as HistoricalCuts

# Missing recovered definitions are rejected until individually reviewed as
# diagnostic-only controls. A control is never counted as a recovered body.
DIAGNOSTIC_ONLY={'ekxj','ekxm','ekxy','ekyf','ek2m','ekyk','ekyl'}
DIAGNOSTIC_ONLY_SEEN=set()
RECOVERED_DEFINITIONS_SEEN=set()


@lru_cache(None)
def diagnostic_controls():
    from pathlib import Path
    import hashlib
    root=Path(__file__).resolve().parents[1]
    controls=json.loads((root/'data/ninth-section-visible-diagnostic-controls-v2.json').read_text(encoding='utf-8'))
    assert controls['schema']=='noema-visible-diagnostic-controls-1'
    assert set(controls['controls'])==DIAGNOSTIC_ONLY
    assert all(not row['source_dependency'] for row in controls['controls'].values())
    assert not controls['derived_control']['source_dependency']
    for path,stamp in controls['source_sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==stamp,path
    return controls

class Cuts:
    arithmetic=HistoricalCuts.arithmetic
    def __init__(self):self.table={}
    def make(self,n):
        n=Q(n);f=FunctionValue(('number',),'truth',lambda q:q<n);self.table[f.implementation]=n;return f
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


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


def forbidden(*xs):raise ValueError('Unknown ninth-section diagnostic input')


def value(x):
    if isinstance(x,DescriptionValue):
        node=renamed(json.loads(x.syntax),{v:k for k,v in mapping().items()})
        if node.get('kind') in ('call','function_ref'):return node['symbol']
        raise ValueError('Unexpected quoted form')
    return x


def relation(rows):return lambda *xs:tuple(value(x) for x in xs) in rows


def unknowns(test,model,names):
    for name in names:
        with pytest.raises(ValueError):test(model|{name:forbidden})


def perturb(test,model,rows,norm=lambda xs:tuple(value(x) for x in xs)):
    count=1;assert test(model)
    for name,rs in rows.items():
        for row in rs:
            assert not test(model|{name:lambda *xs,rs=rs-{row}:norm(xs) in rs});count+=1
            for slot in range(len(row)):
                bad=tuple('wrong' if i==slot else x for i,x in enumerate(row))
                assert not test(model|{name:lambda *xs,rs=(rs-{row})|{bad}:norm(xs) in rs});count+=1
    unknowns(test,model,rows);return count


@lru_cache(None)
def checked_extract_json(serialized,roots,indices):
    extracted=extract_document(json.loads(serialized),roots=roots,statement_indices=list(indices))
    original=extracted.document
    mapped=normalize_document(renamed(original,mapping()))
    recovered={d['name']:d for d in check.restored()['document']['declarations']}
    inverse={v:k for k,v in mapping().items()}
    for i,(old,d) in enumerate(zip(original['declarations'],mapped['declarations'],strict=True)):
        if d['kind']!='definition':continue
        if d['name'] not in recovered and old['name'] in DIAGNOSTIC_ONLY:
            entry=check.catalogs()['einstein-1905'].entries[old['name']]
            assert entry['declaration']==diagnostic_controls()['controls'][old['name']]['declaration']
            assert d==renamed(entry['declaration'],mapping()),('Historical diagnostic expression changed',old['name'])
            DIAGNOSTIC_ONLY_SEEN.add(old['name'])
            continue
        if d['name'] not in recovered and old['name']=='jccw':
            # Independently derived from the unchanged ekxm witness chain in
            # the active catalog; never count this fixture as decoded content.
            expected=diagnostic_controls()['derived_control']['declaration']
            assert d==renamed(expected,mapping()),'Derived historical witness fixture changed'
            DIAGNOSTIC_ONLY_SEEN.add('jccw')
            continue
        actual=deepcopy(recovered[d['name']])
        assert actual==d,('Native definition differs before diagnostic transformation',old['name'])
        RECOVERED_DEFINITIONS_SEEN.add(old['name'])
        original['declarations'][i]=renamed(actual,inverse)
    return extracted


def checked_extract(document,*,roots=(),statement_indices=()):
    return deepcopy(checked_extract_json(json.dumps(document,sort_keys=True),tuple(roots),tuple(statement_indices)))


def native_evaluate(document,*,primitives,**options):
    doc=normalize_document(renamed(document,mapping()))
    return evaluate_document(doc,primitives={mapping().get(n,n):fn for n,fn in primitives.items()},**options)



# These are existing distinguishing diagnostics, evaluated with constructed
# Native values and the actual recovered bodies. Domain abstractions in the
# historical fixture remain explicit and are not proofs over infinite domains.
GROUPS={'attached_material_charge': ('measure_checks', 'pullback_checks', 'binding_checks', 'fixed_checks', 'size_checks'), 'carrier_charge_composition': ('sum_checks', 'partition_checks', 'physical_checks'), 'carrier_field_correspondence': ('location_checks', 'event_checks', 'witness_checks', 'global_checks'), 'charge_constancy_claim': ('chain_checks', 'content_checks', 'presentation_checks'), 'complete_material_attachment': ('amount_checks', 'completeness_checks', 'shared_checks'), 'convective_charge_setting': ('local_checks', 'amount_checks', 'carrier_checks', 'regional_checks'), 'convective_foundation_reading': ('physical_checks', 'global_checks', 'witness_checks', 'naming_checks', 'foundation_checks'), 'convective_relativity_claim': ('law_checks', 'common_law_checks', 'content_checks', 'presentation_checks'), 'convective_transformation_claim': ('binder_checks', 'presentation_checks'), 'convective_transformed_quantities': ('numeric_checks', 'field_checks', 'connection_checks'), 'convective_velocity_interpretation': ('event_checks', 'calibration_checks', 'binder_checks'), 'moving_body_charge_history': ('quantity_checks', 'history_checks', 'pair_checks', 'binder_checks'), 'ninth_section_opening': ('physical_checks', 'equation_checks', 'binder_checks', 'presentation_checks')}

_NAMESPACES={}
_MODULES={}


def native_setup(module,namespace):
    # Retain the historical finite probes. Only unwrap a FunctionValue stored
    # directly inside another Native guard before inspecting its callable.
    import ast,inspect,textwrap
    tree=ast.parse(textwrap.dedent(inspect.getsource(module.setup)))
    candidates=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.While) and ast.unparse(node.test)=='isinstance(x, FunctionValue)':
            if node.body and ast.unparse(node.body[0])=='f = x.implementation':
                candidates.append(node)
    assert len(candidates)==1,module.__name__
    candidates[0].body[1:1]=ast.parse('if isinstance(f,FunctionValue):\n    x=f\n    continue').body
    exec(compile(ast.fix_missing_locations(tree),module.__file__,'exec'),namespace)


def diagnostic_import(name,globals=None,locals=None,fromlist=(),level=0):
    import builtins
    from types import SimpleNamespace
    if level==0 and name.startswith('scripts.check_'):
        proxy=adapted_module(name)
        return proxy if fromlist else SimpleNamespace(**{name.split('.')[1]:proxy})
    if level==0 and fromlist and name=='scripts':
        module=builtins.__import__(name,globals,locals,fromlist,level)
        entries=dict(vars(module))
        for item in fromlist:
            if item.startswith('check_'):entries[item]=adapted_module('scripts.'+item)
        return SimpleNamespace(**entries)
    module=builtins.__import__(name,globals,locals,fromlist,level)
    if level==0 and fromlist and name=='noema.finite_semantics':
        return SimpleNamespace(**(vars(module)|dict(Content=Content,FunctionValue=FunctionValue,
            DescriptionValue=DescriptionValue,SequenceValue=SequenceValue,QuestionValue=QuestionValue,
            evaluate_document=native_evaluate)))
    return module


def adapted_module(module_name):
    # Publish a mutable proxy before recursion: old.prior and cycles must
    # resolve to the cloned namespace, never to the historical module.
    import importlib,builtins
    from types import ModuleType
    if module_name in _MODULES:return _MODULES[module_name]
    module=importlib.import_module(module_name)
    proxy=ModuleType(module_name);ns=proxy.__dict__
    overrides=dict(Content=Content,FunctionValue=FunctionValue,DescriptionValue=DescriptionValue,
        SequenceValue=SequenceValue,QuestionValue=QuestionValue,ConstructedCuts=Cuts,
        value=value,relation=relation,perturb=perturb,unknowns=unknowns,
        extract_document=checked_extract,evaluate_document=native_evaluate)
    # Preserve each historical forbidden-input error message and assertions.
    ns.update(vars(module));ns.update(overrides)
    ns['__builtins__']=vars(builtins)|{'__import__':diagnostic_import}
    _MODULES[module_name]=proxy;_NAMESPACES[module_name]=ns
    imported=[];aliases=[]
    for name,fn in vars(module).items():
        if name in overrides:continue
        if isinstance(fn,ModuleType) and fn.__name__.startswith('scripts.check_'):
            aliases.append((name,fn.__name__));continue
        raw=getattr(fn,'__wrapped__',fn)
        if not isinstance(raw,FunctionType):continue
        owner=raw.__module__
        if owner==module_name:
            copied=FunctionType(raw.__code__,ns,raw.__name__,raw.__defaults__,raw.__closure__)
            copied.__kwdefaults__=raw.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(fn,'cache_info') else copied
        elif owner.startswith('scripts.check_'):
            imported.append((name,owner,raw.__name__))
    for name,owner,original in imported:ns[name]=vars(adapted_module(owner))[original]
    for name,owner in aliases:ns[name]=adapted_module(owner)
    if module_name in ('scripts.check_attached_material_charge',
            'scripts.check_convective_charge_setting','scripts.check_convective_transformed_quantities'):
        native_setup(module,ns)
    if module_name=='scripts.check_calculation_discourse':
        # The fixture's step-cost table uses historical source names. Native
        # quotes retain public names; translate only the fixture comparison.
        ns['symbol']=value
    return proxy


@pytest.mark.parametrize('group,name',[(group,name) for group,names in GROUPS.items() for name in names])
def test_native_physical_bodies_and_distinguishing_bindings(group,name):
    result=vars(adapted_module('scripts.check_'+group))[name]()
    assert isinstance(result,dict) and result.get('cases',0)>0,(group,name,result)


@pytest.mark.parametrize('old',('eisv5','eisv6'))
def test_actual_reference_role_argument_bindings(old):
    # Inspect the actual role before abstracting the other closed references.
    # This checks role argument binding; it does not evaluate quoted physics.
    ds={d['name']:d for d in check.restored()['document']['declarations']}
    target=check.reference_roles()[old]
    assert ds[target]==renamed(check.ROLE_DEFINITIONS[old],mapping())
    needed=set();pending=[target]
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name);pending.extend(_references(ds[name].get('body'))-needed)
    doc=dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[deepcopy(d) for d in ds.values() if d['name'] in needed],statements=[])
    for i,d in enumerate(doc['declarations']):
        if d['name']==target:continue
        if d['kind']=='definition':
            doc['declarations'][i]=dict(kind='primitive',name=d['name'],
                parameters=[p['sort'] for p in d['parameters']],result=d['result'])
    candidate='rolecandidate';context='rolecontext'
    doc['declarations'] += [dict(kind='primitive',name=candidate,parameters=[],result='individual'),
        dict(kind='primitive',name=context,parameters=[],result='situation')]
    doc['statements']=[dict(kind='ask',body=call(target,call(candidate),call(context)))]
    relation_name,row={
        'eisv5':('ekyw',('chosen','case')),
        'eisv6':('eisdv',('eiswl','chosen','eispb','eirf',Q(2),Q(9),'case')),
    }[old]
    constants=('eiswl','eispb','eirf')
    model={mapping()[n]:(lambda n=n:n) for n in constants}
    model.update({candidate:lambda:'chosen',context:lambda:'case'})
    key=mapping()[relation_name]
    def run(expected):
        handlers=model|{key:relation({expected})}
        return evaluate_document(doc,individuals=('chosen','other',*constants),situations=('case','other'),
            primitives={d['name']:handlers.get(d['name'],forbidden) for d in doc['declarations'] if d['kind']=='primitive'},
            memoize_definitions=True,memoize_expressions=True)[0]['value']
    assert run(row)
    for slot in range(len(row)):
        # Change only one argument, including the section level and ordinal.
        bad=list(row);bad[slot]=Q(99) if isinstance(row[slot],Q) else 'wrong'
        assert not run(tuple(bad)),(old,slot)
    if old=='eisv6':
        # A matching heading relation does not identify the section with its
        # containing part. Exercise the explicit inequality independently.
        model[candidate]=lambda:'eispb'
        wrong=list(row);wrong[1]='eispb'
        assert not run(tuple(wrong))
