from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_additive_charge import REPORT,build_report,structural_checks
from scripts.compose_additive_charge import ROOT,PARENT


@pytest.fixture(scope='module')
def result():return build_report()


@pytest.fixture(scope='module')
def documents():return [parse((ROOT/('examples/v014/'+name+'.noema')).read_text(encoding='utf-8')) for name in ('additive-charge','einstein-additive-charge')]


def test_signed_zero_and_restricted_contents_are_allowed(result):
    rows=result['finite']['domain_and_content'];assert len(rows)==12
    for name in ('signed','zero','negative','empty_universe','restricted_domain'):
        assert rows[name]==[True,True]
    assert result['finite']['arbitrary_values_outside_selected_domain_do_not_constrain_content']


def test_domain_requires_empty_set_closure_and_extensionality(result):
    rows=result['finite']['domain_and_content']
    for name in ('missing_empty','not_union_closed','not_difference_closed','domain_depends_on_outside'):
        assert rows[name]==[False,False]


def test_amount_requires_zero_empty_set_disjoint_additivity_and_extensionality(result):
    rows=result['finite']['domain_and_content']
    for name in ('nonzero_empty','wrong_union','total_depends_on_outside'):
        assert rows[name]==[True,False]
    assert result['finite']['all_eight_regions_and_all_region_pairs_quantified']


def test_nonempty_regions_may_cancel_to_zero(result):
    rows=result['finite']['regional_values'];assert len(rows)==16
    assert all(row['result']==(not row['wrong_value']) for row in rows)
    assert any(row['region']==['first','second'] and row['total']==0 and row['result'] for row in rows)
    assert any(row['total']<0 and row['result'] for row in rows)


def test_original_charge_interpretation_and_shared_references_are_required(result):
    bridge=result['bridge'];assert len(bridge['cases'])==3
    assert all(row['result'] for row in bridge['cases'])
    assert len(bridge['contrasts'])==29
    assert not any(bridge['contrasts'].values())
    assert bridge['standalone_agrees']
    assert bridge['unknown_interpretations_refused']


def test_spatial_membership_cannot_depend_on_noncoordinate_values(result):
    assert result['representation']['cases']=={'same_coordinates':True,'hidden_component':False,
        'different_x':True,'outside_time':True,'excluded_region':True}
    assert result['representation']['actual_region_and_point_clause_instantiated']
    assert result['representation']['not_a_full_spatial_domain_proof']


def test_finite_set_check_is_not_a_certificate_for_continuous_space(result):
    assert result['finite']['arithmetic_is_rational_cut_interpretation']
    assert not result['finite']['continuous_space_or_countable_additivity_proved']
    assert result['bridge']['spatial_content_and_representation_are_explicit_contract_oracles']
    assert not result['bridge']['actual_spatial_additivity_proved']
    assert set(result['unbounded'])=={'seor','seow'}
    assert all('rational number domain' in reason for reason in result['unbounded'].values())


@pytest.mark.parametrize('change',['set_scope','distribution','clock','original','representation','units','total','source_route'])
def test_changes_to_scope_and_bindings_are_rejected(documents,change):
    generic,source=deepcopy(documents);ds={d['name']:d for d in source['declarations']}
    def flatten(node):return flatten(node['arguments'][0])+flatten(node['arguments'][1]) if node.get('kind')=='and' else [node]
    parts=flatten(ds['seou']['body']['body'])
    if change=='set_scope':ds['seop']['body']['kind']='exists'
    elif change=='distribution':parts[0]['arguments'][1]=deepcopy(parts[0]['arguments'][0])
    elif change=='clock':parts[1]['arguments'][0]['arguments'][1]=deepcopy(parts[1]['arguments'][0]['arguments'][0])
    elif change=='original':parts[2]['arguments'][0]=deepcopy(parts[2]['arguments'][1])
    elif change=='representation':parts[3]['symbol']='seoq'
    elif change=='units':parts[4]['arguments'][1]['arguments'][2]=deepcopy(parts[4]['arguments'][1]['arguments'][3])
    elif change=='total':parts[4]['arguments'][2]['function']=deepcopy(parts[4]['arguments'][1]['function'])
    else:ds['seov']['body']['arguments'][6]=deepcopy(ds['seov']['body']['arguments'][7])
    with pytest.raises(ValueError):structural_checks(generic,source)


def test_parent_source_roundtrips_and_unfinished_semantics_remain_explicit(result,documents):
    source=documents[1];parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert len(source['declarations'])==len(parent['declarations'])+9
    assert source['statements']==parent['statements']
    assert len(source['statements'])==175
    assert result['new_primitives']==result['new_author_statements']==0
    assert all(result['structure'].values()) and result['roundtrips']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
