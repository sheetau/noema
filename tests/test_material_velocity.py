from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_material_velocity import REPORT,build_report,structural_checks
from scripts.compose_material_velocity import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def source():return parse(source_composed()[0])


def test_signed_velocity_and_acceleration_use_coordinate_time_derivatives(result):
    cases=result['finite']['cases'];assert len(cases)==5
    assert all(row['results']==[True]*4 for row in cases)
    assert any(any(row['quadratic']) for row in cases)
    assert any(row['velocity']==[0,0,0] and any(row['quadratic']) for row in cases)
    assert result['finite']['standalone_agrees']


def test_same_point_does_not_make_another_parameter_coordinate_time(result):
    rows=result['finite']['contrasts'];assert len(rows)==15
    assert rows['proper_parameter']==[True,False,False,True]
    assert rows['wrong_curve_position']==[False,True,False,True]
    for name in ('wrong_ux','wrong_uy','wrong_uz','missing_derivative','missing_history','conflicting_record'):
        assert rows[name]==[True,True,False,True]


def test_history_must_refer_to_the_same_material_point_frame_event_and_context(result):
    for name in ('matter','frame','event','context'):
        assert result['finite']['contrasts']['wrong_'+name]==[False,False,False,True]
    assert result['reverse_probes']['results']==[True,False]
    assert result['reverse_probes']['actual_reverse_clause_instantiated']
    assert result['reverse_probes']['not_a_full_history_proof']


def test_isolated_and_one_sided_domains_do_not_define_ordinary_interior_velocity(result):
    rows=result['finite']['contrasts']
    assert rows['isolated']==[True,False,False,False]
    assert rows['one_sided']==[True,True,False,False]
    assert rows['empty_domain']==[False]*4
    probes=result['interior_probes']['cases'];assert len(probes)==18
    for row in probes:
        assert row['result']==(row['domain']=='baseline' or row['domain']=='one_sided' and row['side']==1)
    assert result['interior_probes']['actual_neighborhood_clause_instantiated']


def test_unknown_and_unbounded_conditions_are_not_replaced_by_samples(result):
    assert result['finite']['unknown_interpretations_refused']
    assert result['finite']['history_and_interior_are_explicit_oracles']
    assert not result['finite']['all_real_history_or_derivative_proved']
    assert set(result['unbounded'])=={'seob','senz','sjs'}
    assert all('rational number domain' in reason for reason in result['unbounded'].values())


def test_old_new_velocity_bridge_keeps_both_histories_and_original_equations(result):
    rows=result['source_bridge']['cases'];assert len(rows)==6
    assert rows['baseline']==[True]
    assert all(row==[False] for name,row in rows.items() if name!='baseline')
    assert result['source_bridge']['formula_and_complete_history_are_contract_oracles']


@pytest.mark.parametrize('change',['interior','reverse','witness','density_velocity','content'])
def test_meaning_changing_factory_and_scope_mutations_are_rejected(source,change):
    doc=deepcopy(source);ds={d['name']:d for d in doc['declarations']}
    if change=='interior':ds['senz']['body']['arguments'][1]['arguments'][1]['kind']='forall'
    elif change=='reverse':ds['seob']['body']['arguments'][1]['arguments'][1]['kind']='exists'
    elif change=='witness':ds['seoe']['body']['body']['arguments'][1]['kind']='forall'
    elif change=='density_velocity':
        body=ds['seoe']['body']['body']['arguments'][1]
        for _ in range(3):body=body['body']
        body['arguments'][7]={'kind':'variable','name':ds['seoe']['body']['parameters'][3]['name']}
    else:ds['seof']['body']['arguments'][1]=ds['seof']['body']['arguments'][2]
    with pytest.raises(ValueError):structural_checks(doc)


def test_source_content_uses_the_constructed_assignment_without_new_author_claims(result,source):
    assert all(result['structure'].values())
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+7
    assert source['statements']==parent['statements']
    assert len(source['statements'])==175
    assert result['new_primitives']==result['new_author_statements']==0
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
