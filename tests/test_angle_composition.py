import hashlib
import json

import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_angle_composition import (
    polynomial_checks, expression_checks, component_checks, source_checks, attribution_checks, alignment,
)
from scripts.compose_angle_composition import ROOT, composed


@pytest.fixture(scope='module')
def expression():
    return expression_checks()['cases']


def test_component_and_angle_formulas_have_conditional_algebraic_connection():
    rows=polynomial_checks()['claims']
    assert len(rows)==10
    for key in ('positive_denominator_recovers_unsquared_expression','polar_components_preserve_squared_magnitude',
        'nonnegative_velocities_are_symmetric','sine_orientation_does_not_change_expression',
        'subluminal_inputs_have_positive_denominator','positive_frame_unsigned_angle_matches_components'):
        assert rows[key]['status']=='valid'
    assert rows['squaring_cannot_select_quotient_sign']['status']=='invalid'
    assert rows['snapshot_sine_denominator_value_is_reviewed_value']['status']=='invalid'


def test_reviewed_cosine_denominator_and_signed_quotient_are_preserved(expression):
    assert expression['parallel']==[True] and expression['snapshot_denominator']==[False]
    assert expression['negative_denominator_signed_value']==[True]
    assert expression['negative_denominator_nonnegative_norm']==expression['negative_root_branch']==[False]


def test_partial_operations_and_degenerate_cases_have_distinct_results(expression):
    for key in ('zero_denominator','negative_radicand','zero_light_speed','negative_magnitude','invalid_circle','invalid_cut'):
        assert expression[key]==[False]
    for key in ('vertical','cancellation','zero_point_speed','zero_frame_speed'):
        assert expression[key]==[True]


def test_direction_changes_and_component_conventions_are_not_conflated(expression):
    for key in ('light_speed_oblique','light_speed_negative_transverse','light_speed_negative_longitudinal'):
        assert expression[key]==[True]
    rows=component_checks()['cases']
    assert rows['negative_transverse']==rows['oriented_negative_sine']==[True]
    assert rows['negative_longitudinal']==[True]
    assert rows['principal_branch_mismatch']==rows['negative_frame_unsigned_mismatch']==[False]


def test_source_formula_uses_same_point_context_and_nonnegative_speed_binding():
    rows=source_checks()['cases']
    assert rows['parallel']==rows['vertical']==rows['cancellation']==[True]
    assert rows['negative_denominator_signed_value']==rows['negative_denominator_nonnegative_norm']==[False]
    for key in ('wrong_motion_scope','wrong_moving_magnitude','wrong_rest_magnitude','wrong_context'):
        assert rows[key]==[False]


def test_formula_is_quoted_in_its_own_source_scope():
    result=attribution_checks();rows=result['cases']
    assert rows['baseline']==[True] and all(value==[False] for key,value in rows.items() if key!='baseline')
    assert result['quoted_formula_not_evaluated_as_truth']


def test_corrected_formula_retains_raw_hash_and_does_not_claim_surrounding_prose():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';before=path.read_bytes()
    result=alignment();row=result['segments'][0]
    assert len(result['segments'])==1 and row['source']=='[M0257]'
    assert row['math_sha256']=='f0ead3799b9a3cbf15b9152e585bd3e24b934322d66b8745d354072609c4bbcc'
    assert row['reviewed_math_sha256']!=row['math_sha256']
    assert row['correction_id']=='einstein-1905:M0257:denominator-cos'
    assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(before).digest()
    assert result['verified_full_units']==0 and result['calculation_transition_and_symmetry_appraisal_unwritten']
    assert result['historical_angle_and_domain_conventions_unresolved']


def test_parent_preservation_basis_and_original_alphabet_roundtrip():
    text,basis=composed();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==(481,709)
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    assert json.loads((ROOT/'data/angle-composition-basis-v1.json').read_text(encoding='utf-8'))==basis
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    parent=parse((ROOT/'examples/v014/einstein-direction-angles.noema').read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements'][:-1]==parent['statements'] and len(doc['statements'])==134
