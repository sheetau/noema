import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_speed_magnitude import polynomial_checks, norm_checks, binding_checks, attribution_checks, alignment
from scripts.compose_speed_magnitude import ROOT, composed


@pytest.fixture(scope='module')
def bindings():
    return binding_checks()['cases']


def test_magnitude_algebra_uses_components_and_nonnegative_branch():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==8
    assert rows['components_determine_magnitude_relation']['status']=='valid'
    assert rows['nonnegative_magnitude_unique']['status']=='valid'
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={'negative_magnitude_branch_is_admissible','sum_of_components_is_magnitude'}
    assert not result['real_cut_field_and_derivative_theorems_proved']


def test_zero_and_negative_components_do_not_imply_negative_speed():
    result=norm_checks();rows=result['norms']
    assert len(rows)==9 and len(result['transformed'])==8
    for name in ('positive','negative_components','mixed_sign','zero','one_zero_component'):
        assert rows[name]==[True]
    for name in ('negative_branch','sum','zero_with_motion','invalid_cut'):
        assert rows[name]==[False]
    assert result['transformed']['cancellation']==[True]
    assert result['transformed']['negative_denominator']==[True]
    assert result['transformed']['negative_result']==[False]
    assert result['transformed']['zero_denominator']==[False]


def test_derivatives_share_functions_time_and_domain(bindings):
    for name in ('baseline','negative_components','zero'):
        assert bindings[name]==[True]*4
    for name in ('swapped_functions','wrong_derivative','different_derivative_time','point_outside_domain','missing_rest_record'):
        assert bindings[name]==[False,True,True,True]
    assert bindings['moving_components_changed']==[True,False,True,True]


def test_quantity_labels_and_physical_methods_are_distinct(bindings):
    assert bindings['wrong_U_label']==[True,True,False,True]
    assert bindings['wrong_w_label']==[True,True,True,False]
    for name in ('wrong_point','wrong_context'):
        assert bindings[name]==[False,False,True,True]
    for name in ('wrong_candidate','negative_candidate'):
        assert bindings[name]==[False]*4


def test_source_naming_does_not_evaluate_or_endorse_methods():
    result=attribution_checks();rows=result['cases']
    assert len(rows)==6 and rows['baseline']==[True,True]
    assert all(value==[False,False] for name,value in rows.items() if name!='baseline')
    assert result['methods_and_labels_quoted_without_evaluation']


def test_only_magnitude_introduction_and_equation_are_counted():
    result=alignment();rows=result['segments']
    assert rows[0]['source']=='Wir setzen:'
    assert {row['unit'] for row in rows}=={'einstein-1905:u0135','einstein-1905:u0136'}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0252'}
    assert result['approximation_and_angle_formula_unwritten']
    assert result['verified_full_units']==0 and not result['facsimile_checked']


def test_parent_definitions_including_derivatives_and_positive_curve_speed_are_preserved():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(477,683)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-motion-question.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-2]==parent['statements'] and len(doc['statements'])==131
