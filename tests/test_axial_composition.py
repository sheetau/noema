import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_axial_composition import (
    polynomial_checks, expression_checks, direction_checks, source_checks, attribution_checks, alignment,
)
from scripts.compose_axial_composition import ROOT, composed


@pytest.fixture(scope='module')
def expression():
    return expression_checks()['cases']


def test_scalar_law_connects_to_components_and_angle_with_explicit_bounds():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==13
    for key in ('axial_components_give_scalar_formula','nonnegative_parallel_angle_matches_scalar_formula',
        'signed_inputs_commute','result_is_unique','zero_is_identity','opposite_subluminal_inputs_cancel',
        'signed_subluminal_denominator_positive','signed_subluminal_result_stays_subluminal'):
        assert rows[key]['status']=='valid'
    for key in ('axis_support_alone_allows_using_magnitude_as_component','zero_denominator_has_a_value',
        'unrestricted_inputs_always_stay_below_light'):
        assert rows[key]['status']=='invalid'
    assert not result['real_cut_field_and_root_laws_proved']


def test_signed_result_and_magnitude_are_distinct(expression):
    for key in ('forward','opposed','negative_result','both_negative','cancellation','negative_denominator'):
        assert expression[key]==[True]
    assert expression['magnitude_substituted']==expression['ordinary_sum']==[False]


def test_expression_domain_is_not_physical_or_direction_domain(expression):
    for key in ('zero_frame','zero_point','both_zero','light_boundary','outside_boost_domain'):
        assert expression[key]==[True]
    for key in ('zero_denominator','zero_light','negative_light','invalid_cut'):
        assert expression[key]==[False]


def test_axial_support_does_not_imply_positive_direction():
    result=direction_checks();rows=result['cases']
    assert rows['forward']==[True,True]
    assert rows['backward']==rows['zero']==rows['wrong_magnitude']==[True,False]
    assert rows['transverse']==rows['oblique']==[False,False]
    assert result['zero_vector_has_axial_support_but_no_positive_direction']


def test_source_conditional_does_not_assert_premise_or_conclusion():
    rows=source_checks()['cases']
    assert rows['forward']==[True]*3
    assert rows['backward_point']==rows['signed_negative_result']==[False,False,True]
    assert rows['zero_frame']==rows['zero_point']==rows['oblique_light']==[False,True,True]
    assert rows['wrong_result']==rows['missing_rest_derivative']==[True,False,False]
    assert rows['wrong_context']==[False,False,True]


def test_direction_condition_and_scalar_conclusion_are_quoted_in_order():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True]
    assert all(row==[False] for key,row in rows.items() if key!='baseline')
    assert result['quoted_direction_and_formula_contents_not_evaluated']


def test_source_range_stops_before_subluminal_and_deficit_argument():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={'einstein-1905:u0141','einstein-1905:u0142'}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0260','M0261','M0262','M0263'}
    clause=next(row['source'] for row in rows if row.get('source','').startswith('Hat auch'))
    assert clause.endswith('so erhalten wir:')
    assert result['positive_direction_is_an_explicit_reading']
    assert result['following_subluminal_prose_and_deficit_argument_unwritten'] and result['verified_full_units']==0


def test_existing_parent_basis_and_original_alphabet_roundtrips():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(490,726)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-calculation-discourse.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements'] and len(doc['statements'])==139
