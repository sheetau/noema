"""Replay original small-domain diagnostics against recovered opening bodies.

Fixture abstractions remain diagnostic boundaries. They neither replace the
published definitions nor prove physical claims over the real domain.
"""
from copy import deepcopy
from contextvars import ContextVar
from functools import lru_cache
from types import FunctionType
import importlib
import json
import pytest
from noema import constructed_semantics as native
from noema.constructed_discourse import normalize_document
from noema.extraction import extract_document
from noema.meaning_catalog import _references
from scripts.shared_modality import renamed
from scripts import check_einstein_early_visible as check
from tests.test_tenth_closing_semantics_visible import RuntimeBoundary as ClosingRuntimeBoundary

RECOVERED_DEFINITIONS_SEEN=set()
ABSTRACTED_DEFINITIONS=set()
RESULTS={}
CONTROL_TRANSFORMS=[]
ACTIVE_DIAGNOSTIC=ContextVar('opening_diagnostic',default=None)
BINDER_CONTROLS={
    ('moving_magnet_case','binding_checks'):{'eidt'},
    ('moving_magnet_case','pointwise_checks'):{'eidn','eidq'},
    ('moving_conductor_case','case_checks'):{'eiec'},
}
CHECKS={
    'electrodynamics_title':('topic_checks','presentation_checks'),
    'sufficient_postulates':('premise_checks','consistency_checks','construction_checks','witness_checks'),
    'ether_dispensability':('vector_checks','negation_checks','dispensability_checks','forecast_checks'),
    'apparent_asymmetry':('appearance_checks','knownness_checks'),
    'interaction_example':('attribution_checks','message_checks','coupling_checks'),
    'observable_contrast':('comparison_checks','distinction_checks','discourse_checks'),
    'moving_magnet_case':('binding_checks','local_checks','pointwise_checks'),
    'moving_conductor_case':('case_checks','comparison_checks','numeric_checks','quantifier_checks'),
    'relativity_conjecture':('grounds_checks','epistemic_checks','restriction_and_motion_checks'),
    'two_postulates':('adoption_and_naming_checks','compatibility_checks','appearance_and_intent_checks'),
    'kinematic_foundation':('referent_checks','claim_checks','scope_checks','sentence_checks'),
    'kinematic_difficulties':('consideration_checks','difficulty_checks','cause_checks','sentence_checks'),
    'kinematics_headings':('simultaneity_checks','topic_checks','presentation_checks'),
    'charge_transport_current':('comparison_checks',),
    'current_distribution':('distribution_checks',),
}


class RuntimeBoundary(ClosingRuntimeBoundary):
    """Recover registered fixture identity through exact Native guard wrappers.

    Unknown functions stay opaque. No extensional sampling or rational-cut
    guessing is used, and Native's guards remain in the evaluated document.
    """
    def convert(self,value,to_native):
        if not to_native and isinstance(value,native.FunctionValue):
            current=value;seen=set()
            while isinstance(current,native.FunctionValue):
                known=self.to_legacy.get(id(current))
                if known is not None:
                    assert known[0] is current
                    self.to_legacy[id(value)]=(value,known[1])
                    return known[1]
                assert id(current) not in seen,'Cyclic Native guard wrapper'
                seen.add(id(current));implementation=current.implementation
                if isinstance(implementation,native.FunctionValue):
                    raw=implementation
                elif (isinstance(implementation,FunctionType)
                      and implementation.__module__=='noema.constructed_semantics'
                      and implementation.__qualname__.endswith('.make_function.<locals>.guarded')):
                    cells=dict(zip(implementation.__code__.co_freevars,
                        (cell.cell_contents for cell in implementation.__closure__)))
                    raw=cells.get('raw')
                    assert isinstance(raw,native.FunctionValue)
                else:break
                assert current.parameters==raw.parameters and current.result==raw.result
                current=raw
        return super().convert(value,to_native)


def checked_control(actual,expected,old,control):
    assert actual is not None,('Unrecovered diagnostic definition',old)
    altered=deepcopy(actual)
    if control==('relativity_conjecture','restriction_and_motion_checks') and old=='eifp':
        slot=expected['body']['body']['arguments'][2]
        assert slot['kind']=='number' and slot['denominator']==1 and slot['numerator'] in (0,2)
        assert altered['body']['body']['arguments'][2]==dict(kind='number',numerator=1,denominator=1)
        altered['body']['body']['arguments'][2]['numerator']=slot['numerator']
        row=dict(root='eifp',kind='order_control',field='body.body.arguments[2].numerator',original=1,diagnostic=slot['numerator'])
    elif old in BINDER_CONTROLS.get(control,set()):
        tail=altered['body']['arguments'][1];binders=[]
        allowed=('exists',) if old=='eiec' else ('forall','exists')
        while tail['kind'] in allowed:
            binders.append(dict(kind=tail['kind'],name=tail['variable'],sort=tail['sort']))
            altered['parameters'].append(dict(name=tail['variable'],sort=tail['sort']))
            tail=tail['body']
        assert binders,'No binder to instantiate'
        altered['body']['arguments'][1]=tail
        row=dict(root=old,kind='binder_instantiation',binders=binders,binding_diagnostics_only=True,full_domain_proof=False)
    else:
        raise AssertionError(('Fixture changed an actual opening body',old))
    assert altered==expected,('Additional change concealed in diagnostic control',old)
    if row not in CONTROL_TRANSFORMS:CONTROL_TRANSFORMS.append(row)


@lru_cache(None)
def mapping():
    return check.names()|{old:check.vocabulary()._symbols[new] for old,new in check.RELATIONS.items()}|check.mapping()


@lru_cache(None)
def recovered():
    return {d['name']:d for d in check.restored()['document']['declarations']}


def checked_extract(document,*,roots=(),statement_indices=()):
    result=extract_document(document,roots=roots,statement_indices=statement_indices)
    mapped=normalize_document(renamed(result.document,mapping()))
    inverse={v:k for k,v in mapping().items()}
    for i,(original,expected) in enumerate(zip(result.document['declarations'],mapped['declarations'],strict=True)):
        if original['kind']!='definition':continue
        actual=recovered().get(expected['name'])
        assert actual==expected,('Unrecovered or changed opening definition',original['name'])
        RECOVERED_DEFINITIONS_SEEN.add(original['name'])
        result.document['declarations'][i]=renamed(deepcopy(actual),inverse)
    return result


@lru_cache(maxsize=128)
def prepared(serialized,control=None):
    """Cache only by complete fixture content, never object identity or mtime."""
    document=json.loads(serialized)
    declarations={d['name']:d for d in document['declarations']}
    needed=set();pending=list(_references(document['statements']))
    while pending:
        name=pending.pop()
        if name in needed:continue
        needed.add(name)
        pending.extend(_references(declarations[name].get('body'))-needed)
    document['declarations']=[d for d in document['declarations'] if d['name'] in needed]
    mapped=normalize_document(renamed(document,mapping()))
    for old,expected in zip(document['declarations'],mapped['declarations'],strict=True):
        if old['kind']=='definition':
            actual=recovered().get(expected['name'])
            if actual==expected:
                RECOVERED_DEFINITIONS_SEEN.add(old['name'])
            else:
                checked_control(actual,expected,old['name'],control)
        elif expected['name'] in recovered() and recovered()[expected['name']]['kind']=='definition':
            ABSTRACTED_DEFINITIONS.add(old['name'])
    return mapped,tuple(d['name'] for d in document['declarations'] if d['kind']=='primitive')


def native_evaluate(document,*,primitives,**options):
    mapped,names=prepared(json.dumps(document,sort_keys=True),ACTIVE_DIAGNOSTIC.get())
    boundary=RuntimeBoundary(mapping())
    # Original FULL fixtures include unrelated retained declarations. Their
    # parse remains validated; the runtime scope is this statement's closure.
    return native.evaluate_document(mapped,
        primitives={mapping().get(n,n):boundary.handler(primitives[n]) for n in names},**options)


@lru_cache(None)
def namespace(stem):
    original=importlib.import_module('scripts.check_'+stem)
    ns=dict(vars(original))
    for name,wrapped in vars(original).items():
        fn=getattr(wrapped,'__wrapped__',wrapped)
        if isinstance(fn,FunctionType) and fn.__module__==original.__name__:
            copied=FunctionType(fn.__code__,ns,name,fn.__defaults__,fn.__closure__)
            copied.__kwdefaults__=fn.__kwdefaults__
            ns[name]=lru_cache(None)(copied) if hasattr(wrapped,'cache_info') else copied
    ns['extract_document']=checked_extract
    ns['evaluate_document']=native_evaluate
    return ns


def test_all_opening_source_definitions_match_recovered_native():
    checked_extract(check.catalogs()['einstein-1905'].document,statement_indices=check.SOURCE_ORDER)
    assert set(check.NEW_DEFINITIONS)<=RECOVERED_DEFINITIONS_SEEN


@pytest.mark.parametrize('stem,name',[(stem,name) for stem,names in CHECKS.items() for name in names])
def test_retained_opening_diagnostics_on_recovered_native(stem,name):
    token=ACTIVE_DIAGNOSTIC.set((stem,name))
    try:result=namespace(stem)[name]()
    finally:ACTIVE_DIAGNOSTIC.reset(token)
    assert isinstance(result,dict) and result
    RESULTS[stem+'.'+name]=result


def test_actual_electric_response_record_with_every_slot_distinguished():
    ns=namespace('electric_response');cuts,model,fields=ns['physical_setup']()
    assert ns['run']('eica',ns['values'](fields,ns['FIELDS']),model)
    count=0
    for (name,_),sort in zip(ns['FIELDS'],ns['sorts']('eica'),strict=True):
        changed=dict(fields);changed[name]=ns['mutate'](fields[name],sort,cuts)
        assert not ns['run']('eica',ns['values'](changed,ns['FIELDS']),model),name
        count+=1
    for name in ('eiro','zzbu','zzbv','eirl','eibf'):
        assert not ns['run']('eica',ns['values'](fields,ns['FIELDS']),model|{name:lambda *xs:False}),name
    RESULTS['electric_response.actual_record']=dict(argument_mutations=count,missing_physical_connections=5,
        full_history_input='eibf',unused_intervention_adapters_not_claimed=True)


def test_complete_current_history_keeps_its_unbounded_domain():
    ns=namespace('charge_transport_current');cuts,model=ns['arithmetic']()
    model.update(zor=lambda:'charge',zm=lambda x:True,eiri=lambda *xs:True)
    values=['body','section','positive','timeunit','chargeunit']
    for offset in (0,5):
        values+=['frame','case',cuts.make(offset),cuts.make(offset+2),lambda t:cuts.make(0),lambda t:cuts.make(0)]
    values+=[cuts.make(5)]
    with pytest.raises(ValueError,match='rational number domain'):
        ns['run']('eibc',values,model,True)
    RESULTS['charge_transport_current.complete_history_refusal']=dict(full_real_domain_refused=True)


def test_general_application_witness_binding_in_a_small_distinguishing_domain():
    ns=namespace('apparent_asymmetry');doc,slots=ns['fixture']('eiex')
    supplied=('a','b','a')  # theory, view, document; reference point is a.
    def run(target):
        model={'jaaref':lambda:'a','eiew':lambda *xs:tuple(xs)==target}
        model.update({n:(lambda x=x:x) for (n,_),x in zip(slots,supplied,strict=True)})
        primitives={d['name']:model.get(d['name'],ns['forbidden']) for d in doc['declarations'] if d['kind']=='primitive'}
        return native_evaluate(doc,individuals=('a','b'),situations=('a','b'),primitives=primitives,
            max_steps=100000,memoize_definitions=False,memoize_expressions=False)[0]['value']
    target=('b','a','a','a','a','a','a','a','a')
    assert run(target)
    # Vary one existential witness at a time, keeping all others instantiated.
    for slot in (1,2,3,4,5):
        changed=list(target);changed[slot]='b'
        assert run(tuple(changed)),slot
    for slot in (0,6,7,8):
        changed=list(target);changed[slot]='b' if target[slot]=='a' else 'a'
        assert not run(tuple(changed)),slot
    assert not run(('outside',)*9)
    RESULTS['apparent_asymmetry.application_binding']=dict(domain_size=2,existential_slots=5,fixed_slots=4,
        binding_diagnostics_only=True,full_domain_proof=False)


def test_diagnostic_order_mutants_cannot_escape_their_explicit_scope():
    doc=deepcopy(namespace('relativity_conjecture')['fixture']('eifp'))
    definition=next(d for d in doc['declarations'] if d['name']=='eifp')
    definition['body']['body']['arguments'][2]['numerator']=0
    serialized=json.dumps(doc,sort_keys=True)
    with pytest.raises(AssertionError,match='Fixture changed'):
        prepared(serialized,None)
    with pytest.raises(AssertionError,match='Fixture changed'):
        prepared(serialized,('relativity_conjecture','epistemic_checks'))
    definition['body']['body']['arguments'][2]['numerator']=3
    with pytest.raises(AssertionError):
        prepared(json.dumps(doc,sort_keys=True),('relativity_conjecture','restriction_and_motion_checks'))


def test_native_guarded_fixture_functions_keep_identity_without_sampling():
    from fractions import Fraction
    from noema import finite_semantics as legacy
    from scripts.check_tau_differential import ConstructedCuts
    cuts=ConstructedCuts();cut=cuts.make(Fraction(2));seen=[]
    opaque=legacy.FunctionValue(('number',),'truth',lambda x:seen.append(x) or True)
    boundary=RuntimeBoundary({});sort=dict(kind='function',parameters=['number'],result='truth')
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=[],result=sort) for n in ('cut','opaque')]+[
        dict(kind='primitive',name=n,parameters=[sort],result='truth') for n in ('capturecut','captureopaque')],
        statements=[dict(kind='ask',body=dict(kind='call',symbol='capture'+n,arguments=[dict(kind='call',symbol=n,arguments=[])])) for n in ('cut','opaque')])
    handlers={'cut':lambda:cut,'opaque':lambda:opaque,'capturecut':lambda x:x is cut and cuts.read(x)==2,
              'captureopaque':lambda x:x is opaque and not seen}
    result=native.evaluate_document(doc,individuals=('a','b'),situations=('a','b'),
        primitives={n:boundary.handler(fn) for n,fn in handlers.items()})
    assert all(r['value'] is True for r in result) and not seen
    unknown=native.FunctionValue(('number',),'truth',lambda x:seen.append(x) or x<2)
    with pytest.raises(ValueError,match='not constructed'):
        cuts.read(boundary.convert(unknown,False))
    assert not seen


def test_pointwise_control_preserves_the_exact_instantiated_body():
    doc=namespace('moving_magnet_case')['fixture']('eidn','pointwise')
    serialized=json.dumps(doc[0],sort_keys=True)
    with pytest.raises(AssertionError,match='Fixture changed'):
        prepared(serialized,None)
    prepared(serialized,('moving_magnet_case','pointwise_checks'))
    actual=recovered()[mapping()['eidn']]
    expected=deepcopy(actual);tail=expected['body']['arguments'][1]
    while tail['kind'] in ('forall','exists'):
        expected['parameters'].append(dict(name=tail['variable'],sort=tail['sort']));tail=tail['body']
    expected['body']['arguments'][1]=tail
    # A valid-looking extra change in the untouched antecedent is forbidden.
    expected['body']['arguments'][0]=deepcopy(tail)
    with pytest.raises(AssertionError,match='Additional change'):
        checked_control(actual,expected,'eidn',('moving_magnet_case','pointwise_checks'))
