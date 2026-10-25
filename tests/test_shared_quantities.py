from copy import deepcopy
from fractions import Fraction
import json
import pytest
from scripts.shared_quantities import *
from scripts.check_shared_quantities import (EXAMPLE,CONSTANTS,PEOPLE,ref,rational,model,values,doc,
    comparison_args,unit_args,evidence_args,amount_call,parts,sum_args,sum_call,partition_call,counted_call,container_call,
    conversion_checks,measurement_checks,partition_checks,binding_diagnostics,partition_bindings,example,example_model)


def test_old_quantity_and_plurality_bodies_are_preserved_with_existing_arithmetic():
    shared={d['name']:d for d in composed()['declarations']}
    for path,names in ((SOURCE,NAMES),(PLURAL,{n:n for n in PLURAL_NAMES})):
        for d in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']:
            if d['name'] in names:
                assert renamed(shared[names[d['name']]],{v:k for k,v in names.items()})==d
    assert len(shared)==30
    assert {n for n,d in shared.items() if d['kind']=='primitive'}==set(ARITHMETIC.values())


def test_public_native_contracts_and_roundtrip_preserve_all_roles_and_types():
    d=composed();b=basis()
    assert parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==d==parse(format_graph(d))
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==b
    assert set(b['definitions'])|set(b['primitives'])==set(b['public_contracts'])=={x['name'] for x in d['declarations']}
    for declaration in d['declarations']:
        contract=b['public_contracts'][declaration['name']]
        expected=declaration['parameters'] if declaration['kind']=='primitive' else [p['sort'] for p in declaration['parameters']]
        assert [r['sort'] for r in contract['arguments']]==expected
        assert contract['result']==declaration['result']
        assert len({r['role'] for r in contract['arguments']})==len(expected)


def test_finite_rational_measurement_and_partition_contrasts():
    assert conversion_checks()['models']==1024
    assert measurement_checks()['models']==48
    assert partition_checks()['models']==64


def test_water_and_rice_examples_use_the_same_quantity_and_container_definitions():
    assert parse((ROOT/EXAMPLE).read_text(encoding='utf-8'))==example()
    assert values(example(),example_model(),CONSTANTS)==[True]*6


def test_measurement_and_partition_binding_diagnostics_cover_every_slot():
    for rows in (binding_diagnostics(),partition_bindings()):
        assert len(rows)==12
        assert all(not r['value'] for r in rows if r['changed_slot'] is not None)


def test_equal_amount_does_not_assert_identical_objects():
    m=model(right=lambda:Fraction(1),measurement=lambda o,k,u,n,w:k=='a' and n*(1 if u=='a' else 2)==2 and w=='now')
    d=doc([call('sameamount',*comparison_args()),op('equal',call('leftsubject'),call('rightsubject'))])
    assert values(d,m)==[True,False]


def test_strict_comparison_uses_scaled_values_and_not_the_raw_readings():
    d=doc([call('sameamount',*comparison_args()),call('amountless',*comparison_args())])
    # 2 units of scale 1 < 3/2 units of scale 2, although 2 > 3/2.
    assert values(d,model())==[False,True]
    m=model(left=lambda:Fraction(3),right=lambda:Fraction(1),measurement=lambda *xs:True)
    assert values(d,m)==[False,False]
    m=model(right=lambda:Fraction(1),measurement=lambda *xs:True)
    assert values(d,m)==[True,False]


@pytest.mark.parametrize('field',['leftkind','leftdim','leftscale','leftunit'])
def test_a_valid_numerical_ratio_cannot_override_the_registered_unit(field):
    m=model()
    m[field]=(lambda a:Fraction(a=='b')) if field=='leftdim' else (lambda:Fraction(2)) if field=='leftscale' else (lambda:'b')
    assert values(doc([amount_call()]),m)==[False]


def test_zero_magnitude_is_allowed_but_negative_is_not_a_physical_amount_here():
    d=doc([amount_call()])
    assert values(d,model(left=lambda:Fraction(0),measurement=lambda *xs:True))==[True]
    assert values(d,model(left=lambda:Fraction(-1),measurement=lambda *xs:True))==[False]
    args=[call('leftkind'),call('rightkind'),ref('leftdim'),ref('rightdim'),num(1),num(1),num(-1),num(-1)]
    assert values(doc([call('quantityequal',*args)]),model())==[True]


def test_correct_sum_cannot_replace_a_complete_disjoint_partition():
    d=doc([sum_call()])
    assert values(d,model())==[True]
    for field in ('partof','disjoint','complete'):
        assert values(d,model(**{field:lambda *xs:False}))==[False]


@pytest.mark.parametrize('missing',['a','b','c'])
def test_every_part_and_the_whole_need_their_own_measurement(missing):
    m=model();original=m['measurement']
    m['measurement']=lambda o,k,u,n,w:o!=missing and original(o,k,u,n,w)
    assert values(doc([sum_call(),counted_call()]),m)==[False,True]


def test_reading_function_is_checked_against_measurements_not_accepted_by_type_alone():
    m=model(readings=lambda o,w:Fraction(100 if o=='c' else 50))
    assert values(doc([sum_call()]),m)==[False]


def test_permutation_preserves_total_but_duplicate_parts_cannot_be_counted_twice():
    reverse=seq(call('rightsubject'),call('leftsubject'))
    duplicate=seq(call('leftsubject'),call('leftsubject'))
    d=doc([sum_call(reverse),sum_call(duplicate)])
    m=model(complete=lambda *xs:True,partof=lambda *xs:True,disjoint=lambda *xs:True,
        readings=lambda o,w:Fraction(4 if o=='c' else 2),measurement=lambda o,k,u,n,w:n==(4 if o=='c' else 2))
    assert values(d,m)==[True,False]


def test_empty_partition_needs_explicit_completeness_and_a_measured_zero_whole():
    d=doc([sum_call(seq()),counted_call(seq(),0)])
    m=model(complete=lambda ps,o,w:not ps.items and o=='c' and w=='now',readings=lambda o,w:Fraction(0),
        measurement=lambda o,k,u,n,w:o=='c' and n==0 and w=='now')
    assert values(d,m)==[True,True]
    m['complete']=lambda *xs:False
    assert values(d,m)==[False,True]
    m['complete']=lambda *xs:True;m['measurement']=lambda *xs:False
    assert values(d,m)==[False,True]


def test_container_count_is_independent_of_contents_magnitude():
    m=model(readings=lambda o,w:Fraction(0),measurement=lambda *xs:False)
    assert values(doc([counted_call(),container_call()]),m)==[True,False]


def test_two_containers_with_the_same_assigned_portion_do_not_double_its_amount():
    m=model(assignment=lambda c:'a',contains=lambda *xs:True,complete=lambda *xs:True,partof=lambda *xs:True,
        disjoint=lambda *xs:True,readings=lambda o,w:Fraction(4 if o=='c' else 2),measurement=lambda *xs:True)
    assert values(doc([counted_call(),container_call()]),m)==[True,False]


def test_mapping_retains_order_and_duplicates_without_a_hidden_set_conversion():
    source=seq(call('leftsubject'),call('rightsubject'),call('leftsubject'))
    expected=seq(call('rightsubject'),call('leftsubject'),call('rightsubject'))
    d=doc([op('equal',call('assignedmembers',source,ref('assignment')),expected)])
    assert values(d,model(assignment=lambda c:'b' if c=='a' else 'a'))==[True]


def test_containment_arguments_cannot_be_reversed():
    m=model(assignment=lambda c:'b' if c=='a' else 'a',contains=lambda p,c,w:(p,c)==('b','a'))
    d=doc([counted_call(seq(call('leftsubject')),1)])
    assert values(d,m)==[True]
    m['contains']=lambda p,c,w:(p,c)==('a','b')
    assert values(d,m)==[False]


@pytest.mark.parametrize('field',['registry','measurement','contains','partof','disjoint','complete'])
def test_relations_cannot_be_combined_from_different_contexts(field):
    m=model();original=m[field]
    m[field]=lambda *xs:original(*xs[:-1],'now') if xs[-1]=='elsewhere' else False
    assert values(doc([container_call()]),m)==[False]


def test_unknown_measurement_is_rejected_under_negation_and_is_not_zero():
    def missing(*xs):raise ValueError('Unknown measurement')
    for field in ('measurement','readings','registry'):
        with pytest.raises(ValueError,match='Unknown'):
            values(doc([op('not',container_call())]),model(**{field:missing}))


def test_amount_negation_does_not_state_that_a_measured_amount_is_zero():
    m=model(left=lambda:Fraction(4))
    zero=call('amountat',call('leftsubject'),*unit_args(),num(0),*evidence_args())
    assert values(doc([op('not',amount_call()),zero]),m)==[True,False]


def test_product_and_quotient_keep_dimensions_and_zero_denominator_condition():
    # All dimensions here are scalar; dimensional identity is checked separately.
    scalar=call('dimensionless')
    ps=[scalar,scalar,scalar,num(1),num(1),num(1)]
    d=doc([call('quantityproduct',*ps,num(2),num(3),num(6)),call('quantityquotient',*ps,num(6),num(3),num(2)),
           call('quantityquotient',*ps,num(0),num(0),num(2))])
    assert values(d,model())==[True,True,False]


def test_unit_conversion_is_not_a_change_of_coordinate_origin():
    compat=[call('leftkind'),call('rightkind'),ref('leftdim'),ref('rightdim'),num(1),num(2)]
    d=doc([call('quantityequal',*compat,num(2),num(1)),call('quantityequal',*compat,num(3),num(2))])
    assert values(d,model())==[True,False]
