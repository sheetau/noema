from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_force_wordings import vector_checks, response_checks, domain_checks, premise_checks, remainder_checks, finite_refusal, source_checks, attribution_checks, alignment
from scripts.compose_force_wordings import ROOT, PARENT, composed, generic_composed


def test_cross_product_keeps_order_zero_parallel_cases_and_electric_addition():
    result=vector_checks();rows=result['cases'];assert len(rows)==12
    assert all(value==[True,True,True,not name.endswith(':wrong_y'),True] for name,value in rows.items())
    assert result['zero_and_parallel_vectors_allowed']


def test_first_order_expression_is_not_an_exact_nonzero_speed_response():
    result=response_checks();rows=result['cases'];assert len(rows)==10
    assert rows['0:linear']==[True,True,True]
    assert rows['3/5:linear']==rows['-3/5:linear']==[True,False,False]
    assert all(rows[n]==[True,True,True] for n in rows if n.endswith(':exact'))


def test_light_speed_and_distinct_axes_are_explicit_domain_conditions():
    rows=domain_checks()['cases'];assert len(rows)==6
    assert all(value==[name=='1:alias=False'] for name,value in rows.items())


def test_moving_unit_point_uses_same_body_event_frame_and_quantity():
    result=premise_checks();rows=result['cases'];assert len(rows)==12
    assert all(value==[name=='baseline'] for name,value in rows.items())
    assert result['motion_uses_the_existing_xm_contract']


def test_second_order_remainder_has_a_rational_uniform_bound_for_fixed_fields():
    result=remainder_checks();assert len(result['claims'])==5
    assert all(r['status']=='valid' for r in result['claims'].values())
    assert result['fixed_field_bounds_not_uniform_over_all_fields']
    assert result['full_real_cut_asymptotic_proof'] is False


def test_finite_examples_cannot_certify_the_asymptotic_condition():
    result=finite_refusal();assert result['refused']
    assert 'Cannot finitely quantify the rational number domain' in result['reason']


def test_comoving_force_uses_transformed_coordinates_and_fields():
    result=source_checks();rows=result['cases'];assert len(rows)==18
    assert rows['baseline']==rows['not_moving_wrong_force']==rows['not_comoving_wrong_force']==[True,True]
    assert rows['bad_asymptotic']==[False,True]
    for n in ('wrong_new_point','wrong_unit','wrong_record','untransformed_force','wrong_force_x','wrong_force_y','wrong_force_z'):
        assert rows[n]==[True,False]
    assert rows['wrong_old_body']==rows['wrong_event']==rows['wrong_context']==[False,False]
    assert result['asymptotic_condition_is_an_explicit_oracle_for_source_wiring']


def test_the_two_quoted_claims_are_not_executed_as_truth():
    result=attribution_checks();rows=result['cases'];assert len(rows)==6
    assert rows['none']==[True,True] and rows['old']==[False,True] and rows['new']==[True,False]
    assert result['quoted_contents_not_executed']


def test_source_alignment_keeps_the_approximation_and_marks_partial_scope():
    result=alignment();assert len(result['segments'])==3
    assert result['segments'][1]['math_id']=='M0318'
    assert 'zweiten und höheren Potenzen' in result['segments'][0]['source']
    assert result['old_wording_is_standard_axis_fixed_field_partial_reading']
    assert result['verified_full_units']==0


def test_all_notations_and_the_entire_parent_are_preserved():
    for builder,counts in ((generic_composed,(7,38,0)),(composed,(590,923,169))):
        text,basis=builder();doc=parse(text);audit=audit_basis(doc,basis)
        assert (audit['primitive_count'],audit['definition_count'],len(doc['statements']))==counts
        assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements']
    byname={d['name']:d for d in doc['declarations']}
    assert all(d==byname[d['name']] for d in parse(generic_composed()[0])['declarations'])
