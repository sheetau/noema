from copy import deepcopy
import json
import pytest
from scripts.shared_revision import *
from scripts.check_shared_revision import (doc,values,model,query,claim,ref,unknown,base,comparison_oracle,
    candidate_checks,comparison_checks,support_checks,choice_checks,binding_diagnostics,
    example,example_model,example_expected,EXAMPLES,EXAMPLE_SCENES)


def test_inventory_preserves_original_bodies_and_meanings():
    d=composed();b=basis();byname={x['name']:x for x in d['declarations']}
    assert len(byname)==28 and len(b['definitions'])==27 and len(MEANINGS)==12
    assert set(b['primitives'])=={'claimchoice'}
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['public_contracts'])==set(byname)
    oldbasis=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    original=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    original['schema_version']=original['lexicon_version']='0.16'
    original['declarations']=[renamed(x,NAMES) for x in original['declarations']]
    for old in normalize_document(original)['declarations']:
        assert byname[old['name']]==old
    for old,new in NAMES.items():assert b['definitions'][new]==oldbasis['definitions'][old]
    shared={x['name']:x for x in parse((ROOT/EVIDENCE).read_text(encoding='utf-8'))['declarations']}
    sharedbasis=json.loads((ROOT/EVIDENCE_BASIS).read_text(encoding='utf-8'))
    for name in REUSED:
        assert byname[name]==shared[name]
        assert b['public_contracts'][name]==sharedbasis['public_contracts'][name]
        assert b['definitions'][name]==sharedbasis['definitions'][name]
    for declaration in raw()['declarations']:
        contract=b['public_contracts'][declaration['name']]
        sorts=declaration['parameters'] if declaration['kind']=='primitive' else [p['sort'] for p in declaration['parameters']]
        assert sorts==[p['sort'] for p in contract['arguments']]
        assert declaration['result']==contract['result']

def test_all_candidate_truth_and_awareness_combinations():
    assert candidate_checks()==dict(models=256,situations=2,checks_per_model=8)

def test_information_and_error_content_classes_with_support_changes():
    assert comparison_checks()==dict(models=1024,items=2,situations=2,support_profiles=4,checks_per_model=4)

def test_stage_specific_access_and_certificates():
    assert support_checks()==dict(models=256,records=2,stages=2,checks_per_model=4)

def test_exact_description_choice_does_not_execute_unknown_content():
    assert len(choice_checks())==18
    assert parse((ROOT/choice.LIBRARY).read_text(encoding='utf-8'))==choice.document()
    assert json.loads((ROOT/choice.BASIS).read_text(encoding='utf-8'))==choice.basis()

def test_each_receipt_and_uptake_slot_with_fixed_other_arguments():
    rows=binding_diagnostics()
    assert len(rows)==21 and all(x['result'] is False for x in rows)

@pytest.mark.parametrize('mode',EXAMPLES)
def test_native_receipt_to_information_comparison(mode):
    assert parse((ROOT/EXAMPLES[mode]).read_text(encoding='utf-8'))==example(mode)
    assert values(example(mode),example_model(mode),EXAMPLE_SCENES)==example_expected(mode)

@pytest.mark.parametrize('field',['adopts','aware','validrecord'])
def test_receipt_alone_does_not_supply_uptake(field):
    assert values(doc([query('evidencereceived'),query('evidenceused')]),model(**{field:lambda *a:False}))==[True,False]

def test_receipt_keeps_an_unevaluated_description():
    assert values(doc([query('evidencereceived')]),model(payload=unknown))==[True]

@pytest.mark.parametrize('name',['evidenceused','beliefupdated','candidatefiltered','informationexpanded','errorscleared'])
def test_truth_dependent_operations_reject_unknown_content(name):
    with pytest.raises(ValueError,match='Unknown'):values(doc([query(name)]),model(payload=unknown))

def test_empty_intersection_is_not_accepted_information():
    m=model(payload=lambda *a:False,alternatives=lambda h,s,w:s=='before')
    assert values(doc([query(n) for n in ('candidatefiltered','evidencereceived','evidenceused','evidencefiltered')]),m)==[True,True,False,False]

def test_same_before_and_after_is_not_a_revision_or_information_expansion():
    bodies=[query(n,after=call('before')) for n in ('evidencereceived','informationpreserved','informationexpanded')]
    assert values(doc(bodies),model(received=lambda *a:True,available=lambda *a:True,precedence=lambda *a:True))==[False,False,False]

def test_an_excluded_assessment_invalidates_information_comparisons():
    names=('informationpreserved','informationexpanded','errorsreduced','errorscleared')
    assert values(doc([query(n) for n in names]),model(comparisons=lambda w:w=='after'))==[False]*4

def test_out_of_scope_added_truth_does_not_increase_information():
    assert values(doc([query('informationexpanded')]),model(scope=lambda i:i=='a'))==[False]

def test_logically_equivalent_error_alias_is_not_error_removal():
    m=model(corpus=lambda h,i,s:i==('a' if s=='before' else 'b'),payload=lambda i,w:w=='after')
    assert values(doc([query('errorsreduced'),query('errorscleared')]),m)==[False,False]

def test_tautological_new_supported_item_adds_no_information():
    assert values(doc([query('informationexpanded')]),model(payload=lambda *a:True))==[False]

@pytest.mark.parametrize('field,value',[('nextholder',call('source')),('nextbefore',call('before')),
    ('nextclaims',lam([('item',I)],claim('firstform'))),
    ('nextcorpus',lam([('h',I),('i',I),('s',S)],truth(False))),
    ('nextsupported',lam([('h',I),('i',I),('s',S)],truth(False)))])
def test_state_link_rejects_a_changed_boundary_or_scoped_information(field,value):
    assert values(doc([query('informationlinked'),query('informationlinked',**{field:value})]),model())==[True,False]

def test_link_scope_does_not_claim_unmentioned_item_identity():
    assert values(doc([query('informationlinked',nextclaims=lam([('item',I)],claim('firstform')))]),model(scope=lambda i:i=='a'))==[True]

def test_quote_identity_is_not_truth_equivalence():
    assert values(doc([query('informationlinked',nextclaims=lam([('item',I)],claim('firstalias')))]),model(scope=lambda i:i=='a'))==[False]

@pytest.mark.parametrize('field',['received','available','precedence','claimchoice'])
def test_missing_interpretation_is_not_false_or_a_default(field):
    with pytest.raises(ValueError,match='Unknown'):values(doc([query('evidencereceived')]),model(**{field:unknown}))

def test_choice_condition_must_be_known_even_when_descriptions_match():
    body=call('claimchoice',call('payload',call('first'),call('before')),claim(),claim())
    with pytest.raises(ValueError,match='Unknown'):values(doc([eq(body,claim())]),model(payload=unknown))

def test_choice_rejects_an_external_non_description_value():
    with pytest.raises((ValueError,TypeError)):
        values(doc([eq(call('claimchoice',truth(True),claim(),claim()),claim())]),model(claimchoice=lambda *a:object()))

def test_native_before_state_is_retained_after_access_and_acceptance_change():
    d=example('filter');d['statements']=[dict(kind='ask',body=dict(kind='apply',function=call('corpus'),
        arguments=[call('agent'),call('first'),call(s)])) for s in ('before','after','before')]
    assert values(d,example_model('filter'),EXAMPLE_SCENES)==[False,True,False]

def test_support_does_not_require_possession_by_the_evidence_author():
    body=dict(kind='apply',function=query('evidencebasis'),arguments=[call('agent'),call('second'),call('after')])
    assert values(doc([body]),model())==[True]
