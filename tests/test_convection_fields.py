import json

import pytest

from noema.grammar import parse,format_graph
from scripts.check_convection_fields import REPORT,build_report,setup_document,model_for,evaluate,expression
from scripts.check_described_appraisals import candidate
from scripts.compose_convection_fields import ROOT,PARENT,REGIONAL,source_composed
from scripts.compose_limits import call as k


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_rational_current_and_density_claims_include_counterexamples(result):
    rows=result['polynomial']['claims']
    assert len(rows)==10
    rejected={'zero_density_does_not_force_zero_velocity','reversing_density_alone_always_preserves_equation','scaled_density_is_not_always_charge'}
    assert {name for name,row in rows.items() if row['status']=='invalid'}==rejected
    assert all(row['status']=='valid' for name,row in rows.items() if name not in rejected)


def test_signed_and_zero_density_bind_to_the_same_twenty_one_partials(result):
    rows=result['binding']['cases']
    assert len(rows)==24
    assert {row['density'] for row in rows}=={'-4','0','4'}
    for row in rows:
        standard=not row['printed_fixture'] or row['light']=='1'
        printed=row['printed_fixture'] or row['light']=='1'
        assert row['results']==[True,standard,printed,True,standard,printed]
        assert row['distinct_partials']==21


def test_unused_magnetic_diagonals_do_not_become_hidden_assumptions(result):
    rows=result['binding']['contrasts']
    used=[]
    for field in ('E','H'):
        for i in range(3):
            for j in range(4):
                row=rows[f'jet_{field}_{i}_{j}']
                if field=='H' and i==j:assert row==[True,True,False,True,True,False]
                else:
                    used.append(row)
                    assert row[3:]==[False,False,False]
    assert len(used)==21


def test_quantity_frame_event_and_context_cannot_be_swapped(result):
    rows=result['binding']['contrasts']
    for name in ('density_value','charge_value','velocity_value','wrong_point','outside_region','swapped_fields','missing_pi',
        'field_frame','field_context','field_region','location_matter','location_frame','location_event','location_context',
        'assignment_matter','assignment_frame','assignment_context','assignment_region'):
        assert rows[name][4:]==[False,False]


def test_printed_missing_factor_is_preserved_as_original_evidence(result):
    review=result['facsimile']
    assert review['images'][0]['printed_page']==916
    assert review['discrepancy']['math_id']=='M0389'
    assert review['discrepancy']['snapshot_matches_facsimile']
    assert not review['discrepancy']['is_transcription_correction']
    assert not review['snapshot_modified']
    assert not review['whole_page_semantics_verified']
    assert review['discrepancy']['preceding_M0383_coefficient']=='1/V'
    assert review['discrepancy']['facsimile_time_derivative_coefficient']=='1'


def test_finite_interpreter_does_not_replace_real_domain_by_sample_points():
    doc=setup_document((ROOT/'examples/v014/convection-fields-core.noema').read_text(encoding='utf-8'))
    doc=candidate(format_graph(doc,'compact'),'q['+k('semj',*(expression(n) for n,_ in REGIONAL))+'].')
    model,_=model_for(doc)
    with pytest.raises(ValueError,match='(?i)finite|enumerat|domain'):
        evaluate(doc,model)


def test_partial_derivative_and_assignment_oracles_are_explicit(result):
    row=result['binding']
    assert row['unknown_inputs_refused'] and row['standalone_agrees']
    assert row['derivatives_use_explicit_affine_oracle']
    assert row['pi_integral_abstracted_with_synthetic_value_three']
    assert row['real_arithmetic_abstracted_to_registered_rational_cuts']
    assert not row['full_real_domain_or_physical_assignment_proved']
    assert not result['polynomial']['full_real_field_transformation_proved']


def test_append_only_parent_and_roundtrips_do_not_certify_semantic_completion(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+15
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
