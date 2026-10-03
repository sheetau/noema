import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_shape_contraction import (
    alignment, attribution_checks, bounds_checks, difference_checks, factor_checks,
    limit_candidate_checks, polynomial_checks, shape_checks,
)
from scripts.compose_shape_contraction import ROOT, generic_composed, source_composed


def test_shape_independent_scaling_and_epsilon_dependent_neighborhood():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==13
    assert {n for n,r in rows.items() if r['status']=='invalid'}=={
        'finite_beta_at_light_speed','finite_beta_above_light_speed',
        'transverse_width_also_contracts','constant_epsilon_independent_neighborhood_suffices'}
    assert not result['general_real_cut_completeness_proved']


def test_tight_bounds_allow_open_and_disconnected_shapes():
    result=bounds_checks();rows=result['cases']
    assert len(rows)==8
    assert {n for n,r in rows.items() if r['status']=='valid'}=={
        'open_interval','singleton','disconnected','translated_contracted_open_interval'}
    assert result['actual_bound_definition_specialized_to_rationals']
    assert result['real_suprema_not_machine_proved']


def test_shape_transform_uses_same_physical_body_and_both_charts():
    result=shape_checks();rows=result['cases']
    assert len(rows)==15
    for name in ('baseline','reverse','stationary'):assert rows[name]==[True]*3
    for name in ('wrong_transform','wrong_shape','wrong_motion','not_rigid','not_stationary'):
        assert rows[name]==[False,True,True]
    for name in ('missing_surface','interior_in_surface','unmeasured_surface','wrong_body',
                 'empty_scope','missing_chart','missing_zero_slice'):
        assert rows[name]==[False,False,True]
    assert result['shape_predicate_defined_in_noema']


def test_coordinate_differences_require_same_observed_time():
    rows=difference_checks()
    assert len(rows)==5 and rows['baseline']['accepted']==[True,True]
    assert rows['baseline']['proper_times']==['3/5','-3/5']
    assert rows['reverse']['proper_times']==['-3/5','3/5']
    assert rows['non_simultaneous']['accepted']==rows['wrong_transform']['accepted']==[False,False]


def test_limit_candidate_depends_on_length_and_precision_without_sampling():
    result=limit_candidate_checks();rows=result['candidates']
    assert len(rows)==4
    assert rows['5:1']['delta']=='5/52'
    assert rows['5:1/10']['delta']=='5/5002'
    assert rows['10:1/10']['delta']=='5/20002'
    assert result['full_cut_limit_refuses_finite_sampling']


def test_real_factor_uses_positive_branch_and_speed_magnitude():
    result=factor_checks();rows=result['cases']
    assert len(rows)==7
    assert rows['baseline']==rows['reverse']==rows['equal_magnitudes']==rows['stationary']==[True,True]
    assert rows['wrong_factor']==rows['light_boundary']==rows['superluminal']==[False,True]
    assert result['monotonicity_is_conditional_on_admissible_ordered_speeds']


def test_limit_interpretation_is_separate_from_regular_and_reversed_claims():
    rows=attribution_checks()
    assert len(rows)==11 and rows['baseline']==[True]*7
    assert rows['wrong_author']==rows['wrong_scope']==rows['wrong_context']==[False]*7
    assert rows['wrong_limit']==[True]*3+[False]+[True]*3
    assert rows['wrong_reverse']==[True]*5+[False,True]
    assert rows['wrong_monotonicity']==[True,True,False]+[True]*4


def test_alignment_excludes_unwritten_forward_reference():
    result=alignment();rows=result['segments']
    assert {r['unit'] for r in rows}=={'einstein-1905:u0116','einstein-1905:u0117'}
    assert {r['math_id'] for r in rows if 'math_id' in r}=={f'M{i:04}' for i in range(201,207)}
    assert result['infinite_velocity_forward_reference_unwritten']
    assert result['boundary_limit_is_explicit_interpretation']
    assert not result['facsimile_checked'] and result['verified_full_units']==0


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,49)),(source_composed,(403,555))])
def test_basis_roundtrip_and_preservation_of_parent(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        parent=parse((ROOT/'examples/v014/einstein-sphere-slice.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
        assert doc['statements'][:-7]==parent['statements'] and len(doc['statements'])==107
