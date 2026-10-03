import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_light_time_arguments import (
    alignment, attribution_checks, expression_checks, polynomial_checks, reciprocal_reuse, source_checks,
)
from scripts.compose_light_time_arguments import ROOT, generic_composed, source_composed


def test_light_paths_and_same_event_labels_give_the_two_elapsed_quotients():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==6
    for name in ('positive_denominator_quotient_unique','positive_label_gives_causal_event_order',
        'affine_candidate_midpoint_iff_coefficient_condition','same_event_coordinates_light_legs_iff_elapsed_quotients'):
        assert rows[name]['status']=='valid'
    assert rows['swapping_elapsed_times_preserves_quotients']['status']=='invalid'
    assert rows['rest_time_is_always_synchronized_moving_time']['status']=='invalid'
    assert not result['tau_formula_derived']


def test_real_positive_reciprocal_reuses_the_existing_definition():
    result=reciprocal_reuse()
    assert result['same_definition_modulo_symbol'] and not result['general_real_field_laws_proved']


def test_complete_tau_arguments_keep_the_two_denominators_and_return_origin():
    result=expression_checks();rows=result['cases']
    assert len(rows)==13
    assert {name for name,row in rows.items() if row['condition']}=={'baseline','shifted_time_origin','negative_label_algebra_only'}
    assert rows['baseline']['argument_tuples']==[[0,0,0,0],[0,0,0,9],[12,0,0,6]]
    assert rows['shifted_time_origin']['argument_tuples']==[[0,0,0,2],[0,0,0,11],[12,0,0,8]]
    assert not rows['light_speed_boundary']['condition']


def test_light_law_is_applied_to_same_selected_segments_and_event_coordinates():
    result=source_checks();rows=result['cases']
    assert len(rows)==31 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')
    assert not rows['different_return_ray'] and not rows['wrong_outward_start_time']
    assert not rows['negative_label']
    assert result['prior_trip_light_law_segment_measurement_charts_and_candidate_are_oracles']
    assert not result['full_physical_derivation_proved']


def test_reformulation_attribution_preserves_premise_and_both_content_descriptions():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']
    assert not any(value for name,value in rows.items() if name!='baseline')


def test_equation_fragments_form_one_partial_reading_not_two_independent_formulas():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={f'einstein-1905:u{i:04}' for i in range(51,54)}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0099','M0100','M0101'}
    assert result['left_and_right_math_fragments_joined'] and not result['facsimile_checked']
    assert not any(row['full_semantic_equivalence'] for row in rows)


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,5)),(source_composed,(281,269))])
def test_basis_roundtrip_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        old=parse((ROOT/'examples/v014/einstein-axial-clock-trip.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(old['declarations'])]==old['declarations']
        assert doc['statements'][:-1]==old['statements'] and len(doc['statements'])==43
