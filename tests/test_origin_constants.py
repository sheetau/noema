import pytest

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_origin_constants import (
    alignment, attribution_checks, context_checks, equation_checks,
    finite_refusals, graph_checks, polynomial_checks, uncertainty_checks,
)
from scripts.compose_origin_constants import ROOT, generic_composed, source_composed


def test_origin_changes_preserve_linear_part_and_difference_law():
    result=polynomial_checks();rows=result['claims']
    assert len(rows)==7
    assert {name for name,row in rows.items() if row['status']=='invalid'}=={
        'changing_constant_by_input_preserves_differences','independent_components_require_a_shared_constant'}
    assert all(row['status'] in ('valid','invalid') for row in rows.values())
    assert not result['general_real_field_proof']


def test_four_constants_are_independent_and_may_be_zero():
    rows=equation_checks()['cases']
    assert len(rows)==13
    assert {name for name,row in rows.items() if row['accepted']}=={
        'independent','all_zero','only_time','only_x','only_y','only_z','negative_constants'}
    assert rows['independent']['second']==['33/8','19/2','13','61/8']


def test_constants_are_shared_across_distinct_inputs_and_full_graph():
    result=graph_checks();rows=result['cases']
    assert len(rows)==9
    assert {name for name,value in rows.items() if value}=={'two_records_common_constants','duplicate_value_alias'}
    assert result['existence_functionality_and_both_directions_evaluated']
    assert result['record_assignment_relations_are_oracles']


def test_changed_setting_preserves_same_event_and_nonadoption_is_not_inequality():
    result=context_checks();rows=result['cases']
    assert len(rows)==6
    assert rows['no_assumption']==[True]*4
    assert rows['assumption_adopted']==rows['conditions_changed']==[True,True,True,False]
    assert rows['different_events']==[False,True,True,True]
    assert rows['wrong_frame']==[False,True,False,True]
    assert rows['wrong_setting']==[False]*4
    assert result['absence_of_assumption_does_not_assert_unequal_origins']


def test_current_normalized_function_can_remain_undetermined():
    result=uncertainty_checks();rows=result['cases']
    assert len(rows)==9 and rows['two_values']==[True,True]
    assert rows['wrong_current_family']==[True,False]
    assert rows['same_at_one_speed']==[False,True]
    assert rows['different_at_another_speed']==[True,True]
    assert rows['old_stage']==rows['outside_domain']==[False,True]
    assert not result['full_epistemic_theory']


def test_infinite_constant_and_function_quantifiers_are_not_sampled():
    rows=finite_refusals()
    assert set(rows)=={'one_constant_tuple_for_all_records','full_normalized_uncertainty'}
    assert all(row['refused'] for row in rows.values())


def test_constant_existentials_are_outside_all_record_pairs():
    text,basis=source_composed();doc=parse(text);decls={d['name']:d for d in doc['declarations']}
    node=decls['spz']['body'];variables=[]
    for _ in range(4):
        assert node['kind']=='exists'
        assert node['sort']=={'kind':'function','parameters':['number'],'result':'truth'}
        variables.append(node['variable']);node=node['body']
    assert node['kind']=='call' and node['symbol']=='spy'
    assert [arg['name'] for arg in node['arguments'][:4]]==variables
    assert len(set(variables))==4
    audit=audit_basis(doc,basis)
    dependencies=audit['definition_dependencies']['definition_primitive_dependencies']
    assert 'zb6' not in dependencies['spz']
    assert {'zfm','zet','zer','zeq'}<=set(dependencies['sqd'])
    assert 'zes' not in dependencies['sqd']


def test_attribution_distinguishes_prior_unknown_function_and_zero_origin_formula():
    rows=attribution_checks()
    assert len(rows)==7 and rows['baseline']==[True,True]
    assert rows['old_unknown_content']==[False,True]
    assert rows['wrong_condition']==rows['zero_origin_conclusion']==[True,False]


def test_source_alignment_remains_partial():
    result=alignment();rows=result['segments']
    assert {row['unit'] for row in rows}=={'einstein-1905:u0085'}
    assert {row['math_id'] for row in rows if 'math_id' in row}=={'M0137','M0138','M0139'}
    assert not result['facsimile_checked'] and result['verified_full_units']==0
    assert result['candidate_family_is_partial_interpretation']


@pytest.mark.parametrize('compose,counts',[(generic_composed,(4,34)),(source_composed,(334,435))])
def test_basis_roundtrips_and_frozen_predecessor(compose,counts):
    text,basis=compose();doc=parse(text);audit=audit_basis(doc,basis)
    assert (audit['primitive_count'],audit['definition_count'])==counts
    assert (ROOT/basis['document']).read_text(encoding='utf-8')==text
    for notation in ('compact','full'):
        form=format_graph(doc,notation)
        assert parse(form)==parse(decode(encode(form,'v2')))==doc
    if compose==source_composed:
        previous=parse((ROOT/'examples/v014/einstein-four-coordinates.noema').read_text(encoding='utf-8'))
        assert doc['declarations'][:len(previous['declarations'])]==previous['declarations']
        assert doc['statements'][:-2]==previous['statements'] and len(doc['statements'])==68
