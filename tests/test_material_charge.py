import json
from fractions import Fraction

import pytest

from noema.grammar import parse
from scripts.check_material_charge import REPORT,build_report,numbers
from scripts.compose_material_charge import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


def test_charge_equality_is_a_consequence_of_density_and_volume_conditions(result):
    claims=result['polynomial']['claims']
    assert len(claims)==8
    for name in ('density_and_slice_volume_factors_cancel','uniform_material_cell_preserves_charge',
        'slice_stretch_is_positive','rest_volume_contracts_by_beta',
        'same_new_time_selects_label_dependent_old_time','slice_affine_map_follows_from_worldline_and_boost'):
        assert claims[name]['status']=='valid'
    for name in ('density_alone_is_invariant','coordinate_volume_is_invariant'):
        assert claims[name]['status']=='invalid'


def test_density_and_volume_can_change_while_charge_does_not(result):
    case=numbers()
    assert case['density']==4 and case['newdensity']==Fraction(22,5)
    assert case['volume']==11 and case['newvolume']==10
    assert case['charge']==case['newcharge']==44
    assert len(result['finite']['cases'])==54
    assert all(r['results']==[True]*7 for r in result['finite']['cases'])


def test_negative_and_zero_charge_do_not_fix_velocity(result):
    rows=result['finite']['cases']
    for row in rows:
        assert Fraction(row['charge'])==11*row['density']
        if row['density']==0:assert Fraction(row['newdensity'])==0
    assert any(r['density']==0 and r['velocity']==[1,-2,3] for r in rows)
    assert any(r['density']<0 for r in rows)


def test_new_simultaneity_does_not_identify_the_old_times(result):
    pair=result['finite']['simultaneous_new_slice']
    assert pair['tau']=='2'
    assert list(map(Fraction,pair['oldtimes']))==[Fraction(43,22),Fraction(23,11)]
    rows=result['finite']['contrasts']
    for name in ('time','tau','x','y','z','xi','eta','zeta','ax','ay','az'):
        assert rows['coordinate_'+name][0] is False
        assert rows['coordinate_'+name][1:5]==[True]*4


def test_wrong_factors_or_totals_break_the_material_cell(result):
    rows=result['finite']['contrasts']
    assert len(rows)==42
    for name in ('stretch','sheary','shearz','newdensity','newvolume','charge','newcharge'):
        assert rows['value_'+name][2:4]==[False,False]
    for name in ('charge','newcharge'):
        assert rows['value_'+name][4] is False


def test_same_numbers_do_not_replace_the_same_matter_frames_and_slices(result):
    rows=result['finite']['contrasts']
    for category,labels in (
        ('old',('matter','frame','slice','density','volume','charge','context')),
        ('new',('matter','frame','slice','density','volume','charge','context')),
        ('pair',('matter','oldframe','newframe','oldslice','newslice','context')),
        ('frame',('oldframe','newframe','speed','context'))):
        for label in labels:assert rows[category+'_'+label]==[True,True,True,False,True,True,True]
    assert result['finite']['unknown_bindings_refused']


def test_singular_slicing_and_nonpositive_volume_are_rejected(result):
    edges=result['finite']['edge_cases'];assert len(edges)==4
    for edge in edges:
        if edge['condition'].startswith('volume='):assert edge['results']==[True,True,False,False,True,True,True]
        else:assert edge['results'][:4]==[False]*4


def test_verification_does_not_claim_general_accelerated_charge_conservation(result):
    assert result['polynomial']['rational_algebra_only']
    assert not result['polynomial']['all_real_cut_laws_proved']
    assert not result['polynomial']['general_volume_change_of_variables_proved']
    assert not result['polynomial']['arbitrary_accelerated_body_conservation_proved']
    assert result['finite']['rational_embeddings_only']
    assert result['finite']['uniform_affine_material_region_only']
    assert not result['alignment']['semantic_completion']
    assert result['alignment']['segments'][0]['status']=='explicit_interpretive_annotation'


def test_parent_roundtrips_and_no_new_author_assertions_are_retained(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+7
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['roundtrips'] and result['finite']['standalone_agrees']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
