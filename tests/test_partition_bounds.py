from copy import deepcopy
import json

import pytest

from noema.grammar import parse
from scripts.check_partition_bounds import REPORT,build_report,polynomial_checks
from scripts.compose_partition_bounds import ROOT,PARENT,generic_composed,source_composed


@pytest.fixture(scope='module')
def result():return build_report()


def test_induction_has_base_step_hypothesis_and_conclusion_bridges(result):
    proof=result['induction'];rows=proof['claims']
    assert len(rows)==13
    assert sum(row['status']=='valid' for row in rows.values())==11
    assert sum(row['status']=='invalid' for row in rows.values())==2
    for name in ('prefix_base_case','prefix_extension','accepted_cell_supplies_step_hypotheses','prefix_invariant_implies_actual_error_bound'):
        assert rows[name]['status']=='valid'
    assert proof['fold_shape']['sum_uses_certified_profile']
    assert proof['fold_shape']['acceptance_binds_all_induction_hypotheses']
    assert proof['fold_shape']['section_polynomial_and_primitive_preserved']
    assert proof['finite_sequence_induction']['scope']=='rational values and arbitrary finite partition length'
    assert proof['finite_sequence_induction']['not_proved']


@pytest.mark.parametrize('symbol,truth,reason',[
    ('seel',True,'Partition acceptance'),
    ('seej',False,'accepted_cell_supplies_step_hypotheses'),
    ('seei',True,'prefix_invariant_implies_actual_error_bound'),
])
def test_deleting_a_guard_or_replacing_invariant_with_true_invalidates_certificate(symbol,truth,reason):
    doc=parse(generic_composed()[0])
    true={'kind':'equal','arguments':[{'kind':'number','numerator':0,'denominator':1}]*2}
    declaration=next(d for d in doc['declarations'] if d['name']==symbol)
    declaration['body']=deepcopy(true if truth else {'kind':'not','arguments':[true]})
    with pytest.raises(ValueError,match=reason):polynomial_checks(doc)


def test_changed_numeric_fold_is_not_certified_by_unrelated_scalar_lemmas():
    doc=parse(generic_composed()[0]);declaration=next(d for d in doc['declarations'] if d['name']=='md')
    declaration['body']['initial']={'kind':'number','numerator':1,'denominator':1}
    with pytest.raises(ValueError,match='preserved tagged partition and sum fold'):polynomial_checks(doc)


def test_finite_partitions_cover_tags_zero_coefficients_and_nonunit_scaling(result):
    rows=result['finite']['cases']
    assert len(rows)==72
    assert all(row['results']==[True,True] for row in rows)
    assert {row['factor'] for row in rows}=={'0','1','2'}
    assert {row['tag'] for row in rows}=={'0','1/2','1'}
    assert len(result['finite']['contrasts'])==9
    assert all(not row[0] for row in result['finite']['contrasts'].values())


def test_actual_constructed_cut_sum_is_evaluated(result):
    rows=result['real_sums']
    assert len(rows['cases'])==18
    assert all(row['results']==[True] for row in rows['cases'])
    assert all(row==[False] for row in rows['contrasts'].values())
    assert rows['actual_noema_sum_and_polynomial_evaluated']
    assert rows['partition_validation_uses_exact_registered_rational_cuts']
    assert rows['standalone_agrees']


def test_mesh_choice_requires_global_premise_and_handles_zero_coefficient(result):
    rows=result['real_bindings']['cases']
    assert len(rows)==24
    assert all(row['results']==[row['global_bound_assumed']] for row in rows)
    assert any(row['factor']==0 and row['global_bound_assumed'] for row in rows)
    assert result['real_bindings']['global_real_partition_bound_is_an_explicit_oracle']
    assert result['real_bindings']['standalone_agrees']


def test_all_real_partitions_are_not_replaced_with_finite_samples(result):
    assert result['unbounded_refusal']['refused']
    assert 'unbounded sequence domain' in result['unbounded_refusal']['reason']


def test_parent_and_claims_preserved(result):
    text,basis=source_composed();doc=parse(text);parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert result['documents'][basis['document']]['primitive_count']==595
    assert result['documents'][basis['document']]['definition_count']==1030
    assert result['sizes']['einstein-partition-bounds']=={'characters':275221,'statements':173}
    assert result['sizes']['partition-bounds-core']=={'characters':4668,'statements':0}
    assert result['new_primitives']==result['new_author_statements']==0


def test_report_reproduces_without_extending_source_completion(result):
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
    assert not result['alignment']['new_source_ranges']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
