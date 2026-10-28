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
from scripts import check_einstein_seventh_section_visible as check
from scripts import seventh_section_visible_profile as profile
from scripts import check_electromotive_wording as source
from scripts import check_vacuum_field_domain as field
from scripts import check_material_relative_frame as material


from scripts.check_tau_differential import ConstructedCuts as HistoricalCuts

# These retained expressions are diagnostic controls, not definitions claimed
# to occur in the circle manuscript. Every other definition must come from the
# recovered Native document. The exact source bodies of these controls are
# checked against the authoritative catalog before constructing a test formula.
DIAGNOSTIC_ONLY={
    'ekbw':'Historical interval-order bug, exercised only as a negative control.',
    'ekcj':'Expanded seven-equation comparison using the recovered transformed components.',
    'ekcm':'Existential setting wrapper used alongside the actual ekcn and ekco binders.',
    'ekex':'Equality comparing the axial and general frequency expressions.',
    'ekgr':'Line-angle cosine comparison for the retained source discrepancy.',
}
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


def forbidden(*xs):raise ValueError('Unknown seventh-section diagnostic input')


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
GROUPS={
 'distant_wave_source':('geometry_checks','support_checks','binding_checks','numeric_checks','witness_checks','presentation_checks'),
 'wave_display':('equation_checks','vector_checks','normal_checks','quantifier_checks','binding_checks','witness_checks','presentation_checks'),
 'wave_inquiry':('interval_checks','region_checks','family_checks','candidate_checks','presentation_checks'),
 'wave_transform_application':('coordinate_checks','event_checks','wave_checks','error_checks','binding_checks','witness_checks','presentation_checks'),
 'observed_doppler':('model_checks','mapping_checks','physical_checks','binding_checks','universal_checks','presentation_checks'),
 'doppler_specialization':('numeric_checks','lift_checks','region_checks','condition_checks','universal_checks','presentation_checks'),
 'doppler_infinity':('point_checks','quantifier_checks','binding_checks','domain_checks','presentation_checks'),
 'aberration_presentation':('motion_checks','scope_checks','binding_checks','universal_checks','presentation_checks'),
 'aberration_specialization':('numeric_checks','condition_checks','universal_checks','presentation_checks'),
 'observed_amplitude':('numeric_checks','binding_checks','quantifier_checks','presentation_checks'),
 'amplitude_specialization':('numeric_checks','condition_checks','universal_checks','presentation_checks'),
 'observed_intensity':('cycle_checks','physical_checks','condition_checks','alternative_checks','universal_checks','presentation_checks'),
 'seventh_section_heading':('setting_checks','heading_checks'),
}
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
    if module_name=='scripts.check_wave_inquiry':
        # CALIBRATION is unchanged; use its declared field list as fixture data.
        from scripts.compose_wave_observer_question import CALIBRATION
        ns['CALIBRATION']=CALIBRATION
        ns['old_binding_setup']=lambda:current_candidate_setup(ns)
    return ns


@pytest.mark.parametrize('group,name',[(group,name) for group,names in GROUPS.items() for name in names])
def test_native_physical_bodies_and_distinguishing_bindings(group,name):
    result=adapted_namespace('scripts.check_'+group)[name]()
    assert isinstance(result,dict) and result.get('cases',0)>0,(group,name,result)
