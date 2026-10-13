from fractions import Fraction as F
import json

import pytest

from noema.grammar import parse
from scripts.check_geometric_volumes import REPORT,build_report
from scripts.compose_geometric_volumes import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_integral_import_preserves_bodies_and_existing_dependencies(result):
    assert result['reuse']['imported_definitions']==7
    assert result['reuse']['body_preserved_under_declared_symbol_mapping']
    assert result['reuse']['interval_validity_and_error_dependencies_match']
    assert result['reuse']['aliases']['cd']=='shv'
    assert result['reuse']['product_absolute_value_and_nonnegative_product_match_after_expanding_zero_comparison']


def test_profile_and_endpoint_algebra_remain_distinct_from_global_calculus(result):
    rows=result['polynomial']['claims']
    assert len(rows)==10
    assert sum(row['status']=='valid' for row in rows.values())==7
    assert sum(row['status']=='invalid' for row in rows.values())==3
    assert not result['polynomial']['fundamental_theorem_or_change_of_variables_proved']
    assert not result['polynomial']['all_real_pi_existence_and_uniqueness_proved']


def test_pi_bounds_are_exact_nested_rational_sums_not_a_fixed_decimal(result):
    rows=result['pi_enclosures']['cases']
    assert [row['partition_cells'] for row in rows]==[4,8,16,32]
    previous=None
    for row in rows:
        lo,hi=F(row['lower']),F(row['upper'])
        assert hi-lo==F(2,row['partition_cells'])==F(row['width'])
        assert row['left_and_right_partitions_checked'] and row['profile_graph_checked_at_every_tag']
        if previous:
            assert previous[0]<lo<hi<previous[1]
        previous=lo,hi
    assert result['pi_enclosures']['finite_enclosures_not_exact_pi']


def test_pi_integral_uses_correct_profile_interval_and_quarter_factor(result):
    rows=result['pi_binding']['cases']
    assert rows=={'bound':[True],'unknown_integral':[False],'wrong_quarter':[False],'wrong_profile':[False]}
    assert result['pi_binding']['oracle_wiring_only_not_certification_of_candidate_three']


def test_sphere_ellipsoid_and_energy_bindings_share_radius_and_coefficient(result):
    rows=result['bindings']['cases']
    assert len(rows)==18
    assert all(row['results']==[True]*4 for row in rows)
    assert result['bindings']['standalone_agrees']
    assert result['bindings']['pi_and_global_integrals_are_assumed_oracles']
    assert result['bindings']['stand_in_constant_is_not_pi']
    assert result['bindings']['not_a_model_of_unabstracted_pi_definition']


def test_missing_pi_integral_and_wrong_bounds_are_not_accepted(result):
    rows=result['bindings']['contrasts']
    assert len(rows)==10
    assert rows['unknown_pi']==[False]*4
    assert rows['missing_integral_premise']==rows['mismatched_integration_bounds']==[False,True,True,True]
    assert rows['wrong_sphere_volume']==[False]*4
    assert rows['wrong_ellipsoid_volume']==[False,True,False,True]
    assert rows['wrong_energy_coefficient']==[True,True,False,False]


def test_geometry_domain_and_zero_density_have_different_requirements(result):
    rows=result['bindings']['contrasts']
    assert rows['zero_radius']==rows['negative_radius']==[False,False,True,True]
    assert rows['nonunit_direction']==[False,True,True,True]
    assert rows['zero_density_and_power']==[True,True,False,True]


def test_unabstracted_pi_and_volume_do_not_run_as_finite_samples(result):
    assert set(result['refusals'])=={'pi','sphere'}
    assert all(row['refused'] for row in result['refusals'].values())


def test_parent_and_original_author_assertions_preserved(result):
    text,basis=source_composed()
    doc,parent=parse(text),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert result['sizes']['einstein-geometric-volumes']=={'characters':273236,'statements':173}
    assert result['sizes']['geometric-volumes-core']=={'characters':7972,'statements':0}
    assert result['documents'][basis['document']]['primitive_count']==595
    assert result['new_primitives']==result['new_author_statements']==0


def test_report_reproduces_without_promoting_partial_source_meaning(result):
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
    assert len(result['alignment']['segments'])==4
    assert all(row['status']=='partial' for row in result['alignment']['segments'])
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips'] and result['parent_preserved']
