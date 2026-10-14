import json

import pytest

from noema.grammar import parse
from scripts.check_adopted_standards import REPORT,build_report
from scripts.compose_adopted_standards import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_dynamic_and_static_standard_evaluation_agree(result):
    rows=result['identity']['cases']
    assert len(rows)==64
    for row in rows:
        required,allowed,forbidden,delivered,first,second=row['states']
        actual=delivered and first and second
        assert row['results']==[required,required and not actual,required and allowed and not forbidden,actual,actual]
    assert result['identity']['dynamic_and_specialized_agree']
    assert result['identity']['standalone_agrees']


def test_same_length_and_same_truth_do_not_replace_an_adopted_description(result):
    rows=result['identity']['description_variants']
    assert [row['criteria'] for row in rows]==[['zu','zt'],['zt','zt'],['zu','zu'],['zy','zu'],['zt'],[],['zt','zu','zt']]
    assert all(row['old_adoption']==[True,True,True,False,False] for row in rows)
    assert all(row['explicit_new_adoption']==[True,False,True,True,True] for row in rows)
    assert result['identity']['list_length_not_used_for_adoption']
    assert result['identity']['exact_description_comparison']


def test_adoption_still_belongs_to_the_same_institution_standard_and_context(result):
    rows=result['identity']['binding_contrasts']
    assert set(rows)=={'adoption_principal','adoption_standard','adoption_context','unadopted'}
    assert all(value==[True,True,True,False,False] for value in rows.values())
    observed=result['identity']['observed_adoption_descriptions']
    assert len(observed)==2 and observed[0]==observed[1] and len(observed[0])==1


def test_static_quotation_preserves_the_existing_safety_rule(result):
    for trace in result['identity']['specialization']:
        assert trace['bound_positions']==[7]
        assert trace['disquotations_removed']==1
        assert trace['quotable_specialized_symbol']=='hzbj'
    assert 'dynamic_constructor_cannot_be_quoted' in result['refusals']
    assert 'unknown_standard_cannot_be_specialized' in result['refusals']


def test_unassessed_criteria_are_not_defaulted_and_norms_do_not_execute_them(result):
    assert result['identity']['unknown_criterion_refused']
    assert result['identity']['norms_do_not_execute_target']
    assert result['identity']['unassessed_message_truth_and_personal_endorsement_not_executed']
    assert not result['identity']['arbitrary_criterion_extensional_equivalence_decided']


def test_source_status_does_not_claim_new_coverage_or_semantic_completion(result):
    assert not result['alignment']['new_source_characters']
    assert not result['alignment']['semantic_completion']
    assert result['alignment']['segments'][0]['status']=='partial'
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}


def test_parent_and_primitives_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+2
    assert result['new_primitives']==result['new_author_statements']==0


def test_report_and_notation_are_reproducible(result):
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
    assert result['roundtrips'] and result['parent_preserved']
