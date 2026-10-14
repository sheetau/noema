import json

import pytest

from noema.grammar import parse
from scripts.check_charge_normalization import REPORT,build_report
from scripts.compose_charge_normalization import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


def test_common_factor_transfers_the_boost_and_preserves_physical_charge(result):
    rows=result['polynomial']['claims'];assert len(rows)==8
    for name in ('common_conversion_transfers_density_boost','converted_material_charge_is_invariant',
        'normalized_old_total_is_scaled_charge','normalized_new_total_is_scaled_charge','normalized_totals_also_agree'):
        assert rows[name]['status']=='valid'
    for name in ('normalized_total_is_physical_charge','different_conversions_still_preserve_physical_charge',
        'zero_density_uniquely_identifies_conversion'):
        assert rows[name]['status']=='invalid'


def test_generic_conversion_is_separate_from_the_pi_specialization(result):
    cases=result['finite']['cases'];assert len(cases)==27
    for row in cases:
        specialized=row['conversion']==12 or row['density']==0
        assert row['results']==[True,True,specialized,specialized,specialized,specialized,True,True,True,True]
    assert result['finite']['pi_oracle_is_synthetic']
    assert not result['finite']['actual_pi_approximated_or_proved']


def test_physical_and_normalized_totals_cannot_be_substituted(result):
    rows=result['finite']['numeric_contrasts'];assert len(rows)==7
    for name in ('physical_density_replaced_by_normalized','new_conversion_doubled'):
        assert rows[name]==[False,False,False,False,False,False,False,False,True,False]


def test_nonpositive_generic_coefficient_does_not_change_the_separate_pi_input(result):
    rows=result['finite']['numeric_contrasts']
    for name in ('conversion_zero','conversion_negative'):
        assert rows[name]==[False,False,True,True,True,True,True,True,True,True]
    assert rows['different_pi']==[True,True,False,False,False,False,True,True,True,True]


def test_diagonal_derivatives_determine_divergence_and_full_jet_assignment_is_bound(result):
    rows=result['finite']['jet_mutations'];assert len(rows)==24
    for row in rows:
        assert row['results']==[True,True,True,True,row['component']!=row['axis'],False,True,True,True,True]
    # An off-diagonal mutation does not affect the trace, but it is a different
    # assigned derivative table even when every compared scalar stays equal.
    assert any(row['component']!=row['axis'] and row['results'][4] for row in rows)


def test_same_matter_frame_slice_and_context_are_required(result):
    rows=result['finite']['binding_contrasts'];assert len(rows)==33
    for side in ('old','new'):
        for field in ('matter','frame','slice','density','volume','charge','context'):
            assert rows[side+'_'+field]==[True,True,True,False,True,False,True,False,True,True]
        for field in ('matter','frame','slice','context'):
            assert rows['trace'+side+'_'+field]==[True,True,True,True,True,False,True,True,True,True]


def test_unknown_pi_and_derivative_bindings_are_not_invented(result):
    assert result['finite']['unknown_relations_and_pi_refused']
    assert result['finite']['binding_contrasts']['missing_pi']==[True,True,False,False,False,False,True,True,True,True]
    assert not result['finite']['full_field_derivatives_or_boost_proved']
    assert not result['polynomial']['actual_pi_value_proved']
    assert not result['polynomial']['all_real_cut_laws_proved']


def test_parent_and_existing_source_range_are_retained(result):
    doc=parse(source_composed()[0]);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+8
    assert result['new_primitives']==result['new_author_statements']==0
    old=json.loads((ROOT/'reports/material-charge-v1.json').read_text(encoding='utf-8'))['alignment']['segments'][0]
    new=result['alignment']['segments'][0]
    assert (new['unit'],new['range'],new['text'])==(old['unit'],old['range'],old['text'])
    assert not result['alignment']['semantic_completion']
    assert result['finite']['standalone_agrees'] and result['roundtrips']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
