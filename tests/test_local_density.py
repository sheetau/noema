from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_local_density import REPORT,build_report,structural_checks,flatten
from scripts.compose_local_density import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse(source_composed()[0])


def test_positive_radius_limit_can_have_signed_or_zero_density(result):
    rows=result['rational']['limits']
    assert {name:row['status'] for name,row in rows.items()}=={
        'affine_right_limit':'valid','wrong_limit':'invalid',
        'negative_constant':'valid','zero_constant':'valid','empty_approach':'invalid'}
    assert result['rational']['rational_comparison_only']
    assert not result['rational']['all_real_ball_density_or_pi_proved']


def test_coordinate_and_charge_scaling_changes_density_value(result):
    assert result['rational']['unit_scaling']['status']=='valid'
    assert result['rational']['density_value_invariant_under_changed_units']['status']=='invalid'


def test_ball_is_spatial_and_simultaneous_with_strict_positive_radius(result):
    assert result['balls']=={name:[name in ('center','inside')] for name in
        ('center','inside','boundary','outside','other_time','zero_radius','negative_radius')}


def test_average_requires_positive_volume_but_allows_negative_or_zero_charge(result):
    rows=result['averages'];assert len(rows)==12
    assert all(row['result'] for row in rows[:9])
    assert all(not row['result'] for row in rows[9:])
    assert any(row['average']=='-4' and row['result'] for row in rows)
    assert any(row['charge']=='0' and row['result'] for row in rows)


def test_profiles_keep_distribution_location_and_units_together(result):
    finite=result['finite'];assert len(finite['cases'])==15
    assert all(row['results']==[True]*3 for row in finite['cases'])
    assert len(finite['contrasts'])==20
    assert all(row==[False,True,False] for row in finite['contrasts'].values())
    assert finite['standalone_agrees']


def test_inconsistent_profiles_limit_normalization_and_pi_are_distinguished(result):
    rows=result['finite']['numeric'];assert len(rows)==7
    for name in ('zero_volume','negative_volume','wrong_average','empty_approach'):
        assert rows[name]==[False,True,False]
    assert rows['wrong_limit']==rows['missing_pi']==[False]*3
    assert rows['wrong_normalized']==[True,False,False]


def test_zero_radius_and_infinite_quantifiers_are_not_sampled_away(result):
    finite=result['finite']
    assert finite['zero_radius_average_not_evaluated']
    assert finite['unknown_interpretations_refused']
    assert finite['profile_limit_and_volume_are_explicit_oracles']
    assert finite['pi_oracle_is_synthetic']
    assert not finite['actual_pi_or_all_real_density_proved']
    assert set(result['unbounded'])=={'seoi','sjr'}
    assert all('rational number domain' in reason for reason in result['unbounded'].values())


@pytest.mark.parametrize('change',['distribution','units','witness','profile_radius','measured_radius','limit_point','content','pi_guard'])
def test_meaning_changing_density_and_content_mutations_are_rejected(source,change):
    doc=deepcopy(source);ds={d['name']:d for d in doc['declarations']}
    if change in ('distribution','units'):
        node=ds['seom']['body']['body']
        for _ in range(6):node=node['body']
        if change=='distribution':node['arguments'][1]=deepcopy(node['arguments'][0])
        else:node['arguments'][6]=deepcopy(node['arguments'][7])
    elif change=='witness':ds['seom']['body']['body']['kind']='forall'
    elif change in ('profile_radius','measured_radius'):
        flatten(ds['seoi' if change=='profile_radius' else 'seok']['body'])[-1]['kind']='exists'
    elif change=='limit_point':
        node=flatten(ds['seoj']['body'])[-1];node['arguments'][2]=deepcopy(node['arguments'][3])
    elif change=='content':
        node=ds['seon']['body']['body']['arguments'][1]['content']
        node['arguments'][1]=deepcopy(node['arguments'][2])
    else:ds['seon']['body']['body']['arguments'][0]['symbol']='ba'
    with pytest.raises(ValueError):structural_checks(doc)


def test_preserved_source_and_roundtrips_do_not_imply_semantic_completion(result,source):
    assert all(result['structure'].values())
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+8
    assert source['statements']==parent['statements']
    assert len(source['statements'])==175
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
