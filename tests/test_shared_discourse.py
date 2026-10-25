from copy import deepcopy
from itertools import product
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.shared_discourse import *
from scripts.check_shared_discourse import (EXAMPLE,EXPECTED,PEOPLE,base,doc,model,values,unknown,num,seq,ref,join,introduce,
    test as clause_test,holds,candidate,unique,apply_expr,sets,identification,introduction_checks,relation_checks,
    scope_checks,identification_bindings,example,example_model)


def test_native_contracts_cover_all_definitions_without_new_individual_constants():
    d=composed();b=basis()
    assert len(d['declarations'])==19 and all(x['kind']=='definition' for x in d['declarations'])
    assert not b['primitives']
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        assert [r['sort'] for r in contract['arguments']]==[p['sort'] for p in declaration['parameters']]
        assert contract['result']==declaration['result']


def test_finite_introductions_relations_and_scope_match_independent_conditions():
    assert introduction_checks()['models']==32
    assert relation_checks()['models']==256
    assert scope_checks()['models']==16


def test_two_topics_and_followup_questions_are_preserved_in_native_example():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model())==EXPECTED


def test_two_independent_existentials_cannot_replace_a_shared_referent():
    p=introduce('arrived');q_=introduce('seated')
    together=join(p,clause_test('seated'))
    m=model(arrived=lambda x,w:x=='a',seated=lambda x,w:x=='b')
    assert values(doc([op('and',holds(p),holds(q_)),holds(together)]),m)==[True,False]


def test_introduction_does_not_choose_a_unique_individual_without_information():
    p=introduce('arrived');m=example_model()
    assert values(doc([holds(p),candidate(p),candidate(p,target='other'),unique(p)]),m)==[True,True,True,False]
    p=join(p,clause_test('seated'))
    assert values(doc([candidate(p),candidate(p,target='other'),unique(p)]),m)==[False,True,True]


def test_distinctness_is_explicit_and_alias_preserves_the_same_individual():
    p=introduce('arrived');m=model(arrived=lambda x,w:x=='a')
    assert values(doc([holds(join(p,introduce('arrived'))),holds(join(p,introduce('arrived',True)))]),m)==[True,False]
    alias=join(p,call('aliasreferent',num(0)))
    equal=lam([('x',I),('y',I),('scene',S)],op('equal',v('x'),v('y')))
    constraint=call('discoursetest',call('referentrelation',num(0),num(1),equal))
    assert values(doc([holds(join(alias,constraint)),candidate(alias,index=1),candidate(alias,index=1,target='other')]),m)==[True,True,False]


def test_missing_negative_fractional_and_out_of_range_indices_never_invent_referents():
    positive=ref('arrived');negative=lam([('x',I),('scene',S)],op('not',call('arrived',v('x'),v('scene'))))
    state=seq(call('known'));indices=[num(-1),dict(kind='number',numerator=1,denominator=2),num(1),num(100)]
    expressions=[]
    for index in indices:
        expressions.append(call('referentavailable',state,index))
        expressions.extend(apply_expr(call('referenttest',index,p),state,call('now')) for p in (positive,negative))
        expressions.append(holds(call('aliasreferent',index),state))
    assert values(doc(expressions),example_model())==[False]*len(expressions)


@pytest.mark.parametrize('boundary',['closeddiscourse','negateddiscourse','alternativediscourse','conditionaldiscourse'])
def test_local_introductions_do_not_escape_but_prior_references_survive(boundary):
    intro=introduce('arrived');tail=clause_test('seated',1)
    block=call(boundary,intro,tail) if boundary=='conditionaldiscourse' else call(boundary,intro,intro) if boundary=='alternativediscourse' else call(boundary,intro)
    m=model(arrived=lambda x,w:boundary!='negateddiscourse',seated=lambda *a:True)
    initial=seq(call('known'))
    assert values(doc([holds(block,initial),candidate(block,index=0,initial=initial),
                       candidate(block,index=1,initial=initial)]),m)==[True,True,False]
    assert values(doc([holds(join(block,clause_test('seated',1)),initial)]),m)==[False]


def test_condition_requires_every_antecedent_assignment_not_just_one_successful_witness():
    conditional=call('conditionaldiscourse',introduce('arrived'),clause_test('seated'))
    assert values(doc([holds(conditional)]),example_model())==[False]
    m=example_model();m['arrived']=lambda *a:False
    assert values(doc([holds(conditional),candidate(conditional)]),m)==[True,False]


def test_nested_introduction_is_available_in_its_consequent_only():
    antecedent=join(introduce('arrived'),introduce('seated'))
    consequence=call('discoursetest',call('referentrelation',num(0),num(1),ref('helped')))
    conditional=call('conditionaldiscourse',antecedent,consequence)
    m=model(arrived=lambda x,w:x=='a',seated=lambda x,w:x=='b',helped=lambda x,y,w:(x,y)==('a','b'))
    assert values(doc([holds(conditional),candidate(conditional,index=0),candidate(conditional,index=1)]),m)==[True,False,False]
    m['helped']=lambda x,y,w:(x,y)==('b','a')
    assert values(doc([holds(conditional)]),m)==[False]


def test_initial_references_are_preserved_and_new_reference_is_appended():
    p=introduce('arrived');initial=seq(call('known'));m=model(arrived=lambda x,w:x=='b')
    assert values(doc([candidate(p,0,'known',initial),candidate(p,0,'other',initial),
                       candidate(p,1,'known',initial),candidate(p,1,'other',initial)]),m)==[True,False,False,True]


def test_introduction_does_not_assert_freshness_from_all_other_domain_individuals():
    p=introduce('arrived',True);m=model(arrived=lambda *a:True)
    assert values(doc([holds(p,empty()),holds(p,seq(call('known'))),holds(p,seq(call('known'),call('other')))]),m)==[True,True,False]


def test_sequence_associativity_retains_ordered_subject_and_object():
    a=introduce('arrived');b=introduce('seated');c=call('discoursetest',call('referentrelation',num(0),num(1),ref('helped')))
    left=join(join(a,b),c);right=join(a,join(b,c))
    d=doc([holds(left),holds(right),candidate(left,0),candidate(right,0),candidate(left,1),candidate(right,1)])
    for p,q_ in product(sets(),repeat=2):
        m=model(arrived=lambda x,w:x in p,seated=lambda x,w:x in q_,helped=lambda x,y,w:x!=y)
        result=values(d,m)
        assert result[0::2]==result[1::2]


def test_swapping_clause_order_is_not_automatic_scope_repair():
    m=example_model()
    assert values(doc([holds(join(introduce('arrived'),clause_test('seated'))),
                       holds(join(clause_test('seated'),introduce('arrived')))]),m)==[True,False]


def test_all_identification_ground_slots_are_bound_and_target_is_not_substituted():
    rows=identification_bindings()
    assert len(rows)==6 and sum(r['values'][0] for r in rows)==1
    chain=join(introduce('arrived'),identification())
    m=model(arrived=lambda x,w:x=='b',identity=lambda *a:True)
    assert values(doc([holds(chain)]),m)==[False]  # known target a is not the introduced b


@pytest.mark.parametrize('relation',['arrived','seated','identity'])
def test_unknown_input_is_neither_nonexistence_nor_failed_identification(relation):
    chain=join(introduce('arrived'),clause_test('seated'),identification())
    m=example_model();m[relation]=unknown
    with pytest.raises(ValueError,match='Unknown'):values(doc([holds(chain)]),m)


def test_followup_question_retains_empty_single_and_multiple_answers():
    update_=introduce('arrived')
    question=call('referentquestion',update_,empty(),num(0),call('now'))
    for candidates in sets():
        m=model(arrived=lambda x,w:x in candidates)
        assert values(doc([question,unique(update_)]),m)==[[[x] for x in PEOPLE if x in candidates],len(candidates)==1]


def test_reference_state_is_explicit_and_no_free_variable_escapes_native_scope():
    d=deepcopy(base());d['statements']=[dict(kind='assert',body=op('equal',v('referent'),v('referent')))]
    with pytest.raises(ValueError,match='Free variable'):normalize_document(d)


def test_world_is_preserved_through_introduction_and_followup():
    chain=join(introduce('arrived'),clause_test('seated'))
    m=model(arrived=lambda x,w:x=='a' and w=='now',seated=lambda x,w:x=='a' and w=='elsewhere')
    assert values(doc([holds(chain)]),m)==[False]
