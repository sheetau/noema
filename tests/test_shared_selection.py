from copy import deepcopy
from fractions import Fraction
import json
import pytest
from scripts.shared_selection import *
from scripts.shared_reference import I,S,truth
from scripts.shared_readings import num
from scripts.shared_plurality import seq
from scripts.check_shared_selection import (doc,model,values,ref,rational,selection_checks,indicator_checks,count_checks,
    example,example_model,field_checks,EXAMPLE,CONSTANTS)


def test_existing_indicator_and_count_bodies_and_shared_dependencies_are_unchanged():
    shared={d['name']:d for d in composed()['declarations']}
    for path,names in ((SOURCE,NAMES),(QUANTITIES,{n:n for n in QUANTITY_NAMES}),(PLURAL,{n:n for n in PLURAL_NAMES})):
        for d in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']:
            if d['name'] in names:
                assert renamed(shared[names[d['name']]],{v:k for k,v in names.items()})==d
    assert len(shared)==9
    assert {n for n,d in shared.items() if d['kind']=='primitive'}=={'rationaladd','rationalmultiply','truthindicator'}


def test_native_contracts_cover_every_signature_and_role():
    d=composed();b=basis()
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['primitives'])|set(b['definitions'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        actual=[p['sort'] for p in declaration['parameters']] if declaration['kind']=='definition' else declaration['parameters']
        record=b['public_contracts'][declaration['name']]
        assert [p['sort'] for p in record['arguments']]==actual
        assert record['result']==declaration['result']


def test_selection_and_counting_have_independent_finite_checks():
    assert selection_checks()['models']==72
    assert count_checks()['models']==124
    assert len(indicator_checks())==16
    assert sum(row['valid'] for row in indicator_checks())==1


def test_native_numeric_fields_keep_both_prior_quantity_examples():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model(),CONSTANTS)==[True]*7
    assert len(field_checks())==6
    kinds={d['name']:d['kind'] for d in example()['declarations']}
    for name in ('readings','volumedimension','massdimension'):
        assert kinds[name]=='definition' and name not in example_model()


@pytest.mark.parametrize('condition',[False,True])
def test_unselected_unknown_numeric_value_is_not_silently_discarded(condition):
    left=call('unknownnumber') if not condition else num(1)
    right=num(2) if not condition else call('unknownnumber')
    d=doc([op('equal',call('selectnumber',truth(condition),left,right),num(1))])
    with pytest.raises(ValueError,match='Unknown'):values(d,model())


def test_unknown_property_is_not_counted_as_zero_even_with_zero_expected_count():
    def unknown(*xs):raise ValueError('Unknown property')
    d=doc([call('countselected',seq(call('first')),ref('property'),num(0))])
    with pytest.raises(ValueError,match='Unknown'):values(d,model(property=unknown))


def test_duplicate_nonselected_individuals_still_make_population_invalid():
    d=doc([call('countselected',seq(call('first'),call('first')),ref('property'),num(0))])
    assert values(d,model(property=lambda x:False))==[False]


def test_empty_population_has_zero_count_but_not_a_positive_or_negative_count():
    d=doc([call('countselected',seq(),ref('property'),num(n)) for n in (0,1,-1)])
    assert values(d,model())==[True,False,False]


def test_numeric_selection_is_ordered_and_preserves_exact_fractions():
    d=doc([op('equal',call('selectnumber',truth(True),rational(Fraction(1,3)),rational(Fraction(-2,7))),rational(Fraction(1,3))),
        op('equal',call('selectnumber',truth(False),rational(Fraction(1,3)),rational(Fraction(-2,7))),rational(Fraction(-2,7)))])
    assert values(d,model())==[True,True]


def test_counting_same_named_individual_twice_is_not_two_distinct_individuals():
    d=doc([call('countselected',seq(call('first'),call('second')),ref('property'),num(2))])
    assert values(d,model(property=lambda x:True))==[True]
    assert values(d,model(property=lambda x:True,second=lambda:'a'))==[False]


def test_corrupt_numeric_field_breaks_quantity_equality_even_when_container_count_survives():
    d=deepcopy(example());field=next(x for x in d['declarations'] if x['name']=='readings')
    field['body']=num(0)
    result=values(normalize_document(d),example_model(),CONSTANTS)
    assert result==[True,True,False,True,True,False,True]


def test_corrupt_dimension_field_is_not_accepted_as_a_matching_registered_unit():
    d=deepcopy(example());field=next(x for x in d['declarations'] if x['name']=='volumedimension');field['body']=num(0)
    result=values(normalize_document(d),example_model(),CONSTANTS)
    assert result==[True,True,False,False,True,True,True]


def test_default_numeric_value_is_not_a_measurement_of_an_unknown_object():
    d=deepcopy(example());d['statements']=[dict(kind='ask',body=call('amountat',call('cupone'),call('volumekind'),call('millilitre'),
        ref('volumedimension'),num(1),call('readings',call('cupone'),call('now')),call('now'),ref('registry'),ref('measurement')))]
    with pytest.raises(ValueError,match='Unknown measurement'):values(d,example_model(),CONSTANTS)
