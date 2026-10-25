from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from scripts.shared_norms import *
from scripts.check_shared_norms import (EXAMPLE,NORMS,CONDITIONS,EXAMPLE_VALUES,base,doc,model,values,ref,quote,key,
    unknown,norm_args,condition_args,witness_args,supported_args,normative_checks,counterfactual_checks,
    comparison_checks,binding_diagnostics,example,example_model)


def test_original_five_norms_and_counterfactual_body_are_preserved():
    shared={d['name']:d for d in composed()['declarations']}
    for path,mapping in ((NORM_SOURCE,NAMES),(COUNTER_SOURCE,COUNTER_NAMES)):
        for d in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']:
            if d['name'] in mapping:
                assert renamed(shared[mapping[d['name']]],{v:k for k,v in mapping.items()})==d
    assert len(shared)==21 and all(d['kind']=='definition' for d in shared.values())


def test_native_and_public_contracts_preserve_all_types_and_roles():
    d=composed();b=basis()
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [r['sort'] for r in contract['arguments']]==[p['sort'] for p in declaration['parameters']]
        assert contract['result']==declaration['result']
        assert len({r['role'] for r in contract['arguments']})==len(declaration['parameters'])


def test_two_topics_distinguish_permission_obligation_conflict_and_performance():
    assert normative_checks()['models']==128
    assert counterfactual_checks()['models']==256
    assert comparison_checks()['models']==256


def test_integrated_two_topics_match_saved_native_example():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model())==EXAMPLE_VALUES


def test_permission_without_execution_and_possible_execution_without_permission():
    first=example();first['statements']=first['statements'][:10]
    m=example_model();observed=values(first,m)
    assert observed[0] and not observed[4]  # allowed lending, no executable method
    m.update(start=lambda *a:True,available=lambda *a:True)
    observed=values(first,m)
    assert observed[9] and not observed[5]  # successful method, no permission to start


def test_permission_and_conflict_do_not_execute_action_but_fulfillment_does():
    m=example_model();m.update(lend=unknown,start=unknown)
    assert values(doc([call(n,*norm_args()) for n in ('permissionclear','notforbidden','normpermitted')]),m)==[True,True,True]
    for name in ('normviolated','normfulfilled'):
        with pytest.raises(ValueError,match='Unknown'):values(doc([call(name,*norm_args())]),m)


@pytest.mark.parametrize('relation,body',[
    ('required',call('notforbidden',*norm_args())),('allowed',call('normpermitted',*norm_args())),
    ('selects',call('conditionalall',*condition_args())),
    ('justifies',call('counterfactualsupported',*supported_args()))])
def test_unknown_input_is_not_a_negative_judgment(relation,body):
    m=example_model();m[relation]=unknown
    with pytest.raises(ValueError,match='Unknown'):values(doc([body]),m)


def test_same_execution_truth_does_not_transfer_description_specific_norms():
    a,b=quote('lendingaction'),quote('otheraction')
    bodies=[op('equal',call('lendingaction',call('person'),call('activity')),call('otheraction',call('person'),call('activity'))),
            op('equal',a,b),call('normpermitted',*norm_args('lendingaction')),call('normpermitted',*norm_args('otheraction'))]
    assert values(doc(bodies),example_model())==[True,False,True,False]


def test_norm_and_comparison_ground_slots_are_bound_in_native_bodies():
    rows=binding_diagnostics()
    assert len(rows)==16 and sum(r['value'] for r in rows)==2


def test_grounded_rule_needs_one_same_norm_and_explicit_reason():
    d=doc([call('normrequired',*norm_args('startingaction',grounded=True))])
    for recognized,applicable,supports in product((False,True),repeat=3):
        m=example_model()
        for name,enabled in (('recognized',recognized),('applicable',applicable),('supports',supports)):
            if not enabled:m[name]=lambda *a:False
        assert values(d,m)==[recognized and applicable and supports]
    m=example_model();m['applicable']=lambda n,p,r,w:(n,p,r,w)==('b','b','a','now')
    assert values(d,m)==[False]  # a is recognized and supported; only b applies
    m=example_model();m['supports']=lambda n,r,*a:n=='b' and r=='b'
    assert values(d,m)==[False]  # cannot borrow the grounds of a different norm


@pytest.mark.parametrize('relation,baseline,replacements',[
    ('recognized',('a','a','now'),('b','b','left')),
    ('applicable',('a','b','a','now'),('b','a','b','left'))])
def test_recognition_and_applicability_slots_use_the_same_context(relation,baseline,replacements):
    d=doc([call('normwitness',*witness_args())])
    for slot in range(len(baseline)):
        expected=list(baseline);expected[slot]=replacements[slot]
        m=model(recognized=lambda *a:True,applicable=lambda *a:True,supports=lambda *a:True)
        m[relation]=lambda *a,e=tuple(expected):a==e
        assert values(d,m)==[False]


def test_absent_or_inconsistent_comparison_is_not_vacuous_success():
    d=doc([call(n,*condition_args()) for n in CONDITIONS])
    m=example_model();m['selects']=lambda *a:False
    assert values(d,m)==[False]*4
    m['selects']=lambda a,w:w=='now'  # actual antecedent is false
    assert values(d,m)==[False]*4


def test_antecedent_and_consequent_cannot_use_different_witnesses():
    m=example_model();m.update(selects=lambda a,w:w!='now',offered=lambda w:w=='left',received=lambda w:w=='right')
    assert values(doc([call(n,*condition_args()) for n in CONDITIONS]),m)==[False]*4


def test_actual_antecedent_is_required_false_only_for_contrary_reading():
    m=example_model();m.update(offered=lambda w:True,received=lambda w:True)
    assert values(doc([call(n,*condition_args()) for n in CONDITIONS]),m)==[True,True,True,False]
    for actual_consequence in (False,True):
        m.update(offered=lambda w:w!='now',received=lambda w:actual_consequence if w=='now' else True)
        assert values(doc([call('contraryconditional',*condition_args())]),m)==[True]


def test_best_selection_keeps_ties_and_does_not_follow_consequent_success():
    best=call('comparisonbest',ref('offered'),ref('eligible'),ref('closer'))
    d=doc([call(n,*condition_args(selector=best)) for n in ('conditionalall','conditionalmight')])
    m=example_model()
    assert values(d,m)==[False,True]  # both equally preferred, only left succeeds
    m['closer']=lambda a,x,y:(x,y)==('left','right')
    assert values(d,m)==[True,True]
    m['closer']=lambda a,x,y:(x,y)==('right','left')
    assert values(d,m)==[False,False]  # preferred right is retained although unsuccessful


def test_nontransitive_three_candidate_preference_is_rejected():
    m=example_model();m.update(offered=lambda w:True,eligible=lambda *a:True,
        closer=lambda a,x,y:(x,y) in {('now','left'),('left','right')})
    ordered=call('comparisonordered',call('context'),ref('offered'),ref('eligible'),ref('closer'))
    assert values(doc([ordered]),m)==[False]
    m['closer']=lambda a,x,y:(x,y) in {('now','left'),('left','right'),('now','right')}
    assert values(doc([ordered]),m)==[True]


def test_ordered_conditionals_connect_order_check_to_comparison_result():
    bodies=[call(n,call('context'),ref('offered'),ref('received'),ref('eligible'),ref('closer'))
            for n in ('orderedconditional','orderedmight')]
    m=example_model()
    assert values(doc(bodies),m)==[False,True]
    m.update(offered=lambda w:True,eligible=lambda *a:True,received=lambda w:True,
        closer=lambda a,x,y:(x,y) in {('now','left'),('left','right')})
    assert values(doc(bodies),m)==[False,False]  # a best candidate exists, but preference is nontransitive
    m['closer']=lambda a,x,y:(x,y) in {('now','left'),('left','right'),('now','right')}
    assert values(doc(bodies),m)==[True,True]


def test_cyclic_preference_has_no_best_world_and_no_successful_conditional():
    best=call('comparisonbest',ref('offered'),ref('eligible'),ref('closer'))
    m=example_model();m['closer']=lambda a,x,y:x!=y
    assert values(doc([call('conditionalall',*condition_args(selector=best))]),m)==[False]


def test_supported_counterfactual_uses_quoted_premise_itself():
    args_=supported_args();args_[1]=quote('switched')
    m=example_model();m['switched']=lambda w:False
    assert values(doc([call('counterfactualsupported',*args_)]),m)==[False]
    # Even coextensive premises retain different quoted identities in their grounds.
    m['switched']=m['offered']
    assert values(doc([call('counterfactualsupported',*args_)]),m)==[False]
