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
from scripts import check_einstein_eighth_section_visible as check
from scripts import eighth_section_visible_profile as profile
from scripts import check_electromotive_wording as source
from scripts import check_vacuum_field_domain as field
from scripts import check_material_relative_frame as material


from scripts.check_tau_differential import ConstructedCuts as HistoricalCuts

# Missing recovered definitions are rejected until individually reviewed as
# diagnostic-only controls. A control is never counted as a recovered body.
DIAGNOSTIC_ONLY={}
DIAGNOSTIC_ONLY_SEEN=set()
RECOVERED_DEFINITIONS_SEEN=set()

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


def forbidden(*xs):raise ValueError('Unknown eighth-section diagnostic input')


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
            assert d==renamed(entry['declaration'],mapping()),('Historical diagnostic expression changed',old['name'])
            DIAGNOSTIC_ONLY_SEEN.add(old['name'])
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
GROUPS={'eighth_section_heading': ('correspondence_checks', 'heading_checks'), 'energy_frequency_law': ('numeric_checks', 'binding_checks', 'appraisal_checks', 'presentation_checks'), 'light_ellipsoid_surface': ('affine_checks', 'geometry_checks', 'quantifier_checks', 'polynomial_checks', 'presentation_checks'), 'light_energy_ratio': ('numeric_checks', 'physical_checks', 'binding_checks', 'polynomial_checks', 'presentation_checks'), 'light_volume_ratio': ('numeric_checks', 'binding_checks', 'polynomial_checks', 'presentation_checks', 'chain_checks'), 'mirror_energy_principle': ('budget_checks', 'equation_checks', 'quantifier_checks', 'presentation_checks'), 'mirror_wave_quantities': ('binding_checks', 'equation_checks', 'literal_angle_checks', 'quantifier_checks', 'presentation_checks'), 'optical_problem_method': ('reconstruction_checks', 'witness_checks', 'method_checks', 'scope_checks', 'presentation_checks'), 'perfect_mirror_setting': ('flow_checks', 'region_checks', 'physical_checks', 'quantifier_checks', 'presentation_checks'), 'portion_energy_inquiry': ('setting_checks', 'identity_checks', 'candidate_checks', 'question_checks', 'presentation_checks'), 'pressure_leading_approximation': ('analytic_checks', 'quantifier_checks', 'agreement_checks', 'presentation_checks'), 'reflected_light_inquiry': ('return_checks', 'coverage_checks', 'setting_checks', 'candidate_checks', 'question_checks', 'presentation_checks'), 'reflected_return_quantities': ('binding_checks', 'equation_checks', 'disagreement_checks', 'quantifier_checks', 'presentation_checks'), 'same_light_portion': ('transport_checks', 'physical_checks', 'quantifier_checks', 'presentation_checks', 'reading_checks')}
_NAMESPACES={}


def diagnostic_import(name,globals=None,locals=None,fromlist=(),level=0):
    import builtins
    from types import SimpleNamespace
    if level==0 and fromlist and name.startswith('scripts.check_'):
        return SimpleNamespace(**adapted_namespace(name))
    module=builtins.__import__(name,globals,locals,fromlist,level)
    if level==0 and fromlist and name=='noema.finite_semantics':
        return SimpleNamespace(**(vars(module)|dict(Content=Content,FunctionValue=FunctionValue,
            DescriptionValue=DescriptionValue,SequenceValue=SequenceValue,QuestionValue=QuestionValue,
            evaluate_document=native_evaluate)))
    return module


def current_candidate_setup(ns):
    # The historical helper only used its obsolete fixture to obtain argument
    # slots. Obtain those same slots from the actual corrected candidate ekcc.
    cuts,model=ns['numbers']();fields=ns['QUESTION']+ns['ANSWERS'];slots=ns['fixture']('ekcc')[1]
    assert len(fields)==len(slots)
    values=[n if t=='a' else 'case' if t=='d' else ns['sentinel'](s,i+1,cuts)
        for i,((n,t),(_,s)) in enumerate(zip(fields,slots,strict=True))]
    positions={n:i for i,(n,t) in enumerate(fields)}
    def gate(names):
        return lambda *xs:len(xs)==len(names) and all(ns['same_value'](x,values[positions[n]],slots[positions[n]][1],cuts) for x,n in zip(xs,names))
    rows={'ekbx':[n for n,t in ns['INVESTIGATION']],'ejsn':[n for n,t in ns['CALIBRATION']],
        'eispn':['process','frame','electricfield','magneticfield','region','context']}
    return cuts,values,slots,model|{n:gate(names) for n,names in rows.items()},gate


def fixture_identity(x,cuts):
    # Compare issued fixture identities, never extensional function equality.
    if isinstance(x,(tuple,list)):return tuple(fixture_identity(v,cuts) for v in x)
    if isinstance(x,SequenceValue):return tuple(fixture_identity(v,cuts) for v in x.items)
    if isinstance(x,FunctionValue):
        try:return cuts.read(x)
        except ValueError:pass
        while isinstance(x,FunctionValue):
            fn=x.implementation
            if isinstance(fn,FunctionValue):x=fn;continue
            code=getattr(fn,'__code__',None)
            if code is None:return fn
            closed=dict(zip(code.co_freevars,(c.cell_contents for c in (getattr(fn,'__closure__',None) or ()))))
            if 'raw' not in closed:return fn
            x=closed['raw']
    return x


def native_method_checks(module,ns):
    # The historical local key stops at a nested FunctionValue. Native guards
    # may wrap that value directly. Replace only this identity helper; retain
    # every assertion and model in the original diagnostic.
    import ast,inspect,textwrap
    raw=module.method_checks.__wrapped__
    tree=ast.parse(textwrap.dedent(inspect.getsource(raw)))
    function=tree.body[0];function.decorator_list=[]
    keys=[n for n in function.body if isinstance(n,ast.FunctionDef) and n.name=='key']
    assert len(keys)==1 and [a.arg for a in keys[0].args.args]==['x']
    key=keys[0]
    assert 'raw' in ast.unparse(key) and 'cuts.read(x)' in ast.unparse(key)
    key.body=ast.parse('return fixture_identity(x,cuts)').body
    ns['fixture_identity']=fixture_identity
    exec(compile(ast.fix_missing_locations(tree),module.__file__,'exec'),ns)
    ns['method_checks']=lru_cache(None)(ns['method_checks'])


def adapted_namespace(module_name):
    # Clone functions into isolated namespaces, including imported diagnostic
    # helpers. Do not patch historical validators or reuse their cached results.
    import importlib,builtins
    if module_name in _NAMESPACES:return _NAMESPACES[module_name]
    module=importlib.import_module(module_name)
    overrides=dict(Content=Content,FunctionValue=FunctionValue,DescriptionValue=DescriptionValue,
        SequenceValue=SequenceValue,QuestionValue=QuestionValue,ConstructedCuts=Cuts,
        value=value,relation=relation,perturb=perturb,unknowns=unknowns,forbidden=forbidden,
        extract_document=checked_extract,evaluate_document=native_evaluate)
    if module_name in ('scripts.check_optical_problem_method','scripts.check_portion_energy_inquiry'):
        # Its negative-control test checks this validator's own error message.
        overrides['forbidden']=module.forbidden
    ns=dict(vars(module))|overrides
    ns['__builtins__']=vars(builtins)|{'__import__':diagnostic_import}
    _NAMESPACES[module_name]=ns
    imported=[]
    for name,fn in vars(module).items():
        if name in overrides:continue
        raw=getattr(fn,'__wrapped__',fn)
        if not isinstance(raw,FunctionType):continue
        owner=raw.__module__
        if owner==module_name:
            copied=FunctionType(raw.__code__,ns,raw.__name__,raw.__defaults__,raw.__closure__)
            copied.__kwdefaults__=raw.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(fn,'cache_info') else copied
        elif owner.startswith('scripts.check_'):
            imported.append((name,owner,raw.__name__))
    for name,owner,original in imported:ns[name]=adapted_namespace(owner)[original]
    if module_name=='scripts.check_optical_problem_method':native_method_checks(module,ns)
    if module_name=='scripts.check_calculation_discourse':
        # Quoted steps carry public Native symbols; compare their source names
        # only inside this diagnostic fixture, preserving the quoted syntax.
        ns['symbol']=value
    if module_name=='scripts.check_wave_inquiry':
        # CALIBRATION is unchanged; use its declared field list as fixture data.
        from scripts.compose_wave_observer_question import CALIBRATION
        ns['CALIBRATION']=CALIBRATION
        ns['old_binding_setup']=lambda:current_candidate_setup(ns)
    return ns


@pytest.mark.parametrize('group,name',[(group,name) for group,names in GROUPS.items() for name in names])
def test_native_physical_bodies_and_distinguishing_bindings(group,name):
    result=adapted_namespace('scripts.check_'+group)[name]()
    assert isinstance(result,dict),(group,name,result)
    if name=='polynomial_checks':
        assert group in ('light_ellipsoid_surface','light_energy_ratio','light_volume_ratio')
        assert result['rational_polynomial_only'] is True and result['lemmas']
        assert all(row['status']=='valid' for row in result['lemmas'].values())
    elif (group,name)==('same_light_portion','reading_checks'):
        assert result==dict(cross_unit_prose_characters=242,cross_unit_math_elements=2,
            u0205_additional_prose_characters=94,source_crossing_display_and_semicolon_preserved=True,
            whole_unit_reviews_separate=True)
    else:assert result.get('cases',0)>0,(group,name,result)


@pytest.mark.parametrize('old',('eistk','eisve','eisvf','eisvp','zvaa'))
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
        'eistk':('eisdv',('eisvw','chosen','eispb','eirf',Q(2),Q(8),'case')),
        'eisve':('eisvc',('chosen','eku5','eistk','case')),
        'eisvf':('eisbn',('eku3','chosen',Q(0),'case')),
        'eisvp':('eisvq',('chosen','eisuu','ekti','eirf','case')),
        'zvaa':('eisd3',('eistn','chosen','eirf','case')),
    }[old]
    constants=('eisvw','eispb','eirf','eistk','eisuu','eistn')
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
