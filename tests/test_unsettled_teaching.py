import json

import pytest

from noema.grammar import parse
from scripts.check_unsettled_teaching import REPORT,build_report
from scripts.compose_unsettled_teaching import ROOT,PARENT,source_composed


@pytest.fixture(scope='module')
def result():
    return build_report()


def test_empty_candidates_are_neither_settled_acceptance_nor_counterevidence(result):
    rows=result['finite']['judgment_cases']
    assert len(rows)==32
    for row in rows:
        selected=[a for chosen,a in zip(row['selected'],row['endorsement']) if chosen]
        settled=bool(selected) and all(selected)
        counter=any(not a for a in selected)
        rejected=bool(selected) and all(not a for a in selected)
        mixed=any(selected) and counter
        assert row['results'][:4]==[settled,counter,rejected,mixed]
        assert row['results'][-1]==row['actual_endorsement']
        if not selected:assert row['results'][:4]==[False]*4


def test_possible_truth_needs_a_selected_world_and_a_contained_true_claim(result):
    rows=result['finite']['possibility_cases']
    assert len(rows)==256
    for row in rows:
        possible=any(row['selected'][world] and claim in row['parts'] and row['truth'][2*part+world]
            for part,claim in enumerate(('c1','c2')) for world in range(2))
        assert row['results'][4:6]==[possible,any(row['selected']) and not possible]
        assert row['results'][6] is False
        assert row['results'][7:9]==[possible,possible]


def test_some_truth_does_not_require_all_parts_to_be_true(result):
    row=next(row for row in result['finite']['possibility_cases'] if row['parts']==['c1','c2'] and
        row['selected']==[True,True] and row['truth']==[True,False,False,False])
    assert row['results'][4] is True
    assert row['results'][6] is False


def test_current_truth_does_not_determine_the_modal_claim(result):
    rows=result['finite']['actual_truth_cases']
    assert len(rows)==4
    for row in rows:
        assert row['results'][4:8]==[True,False,any(row['truth']),True]


def test_subject_document_anchor_and_fixed_parts_are_not_swapped(result):
    rows=result['finite']['binding_contrasts']
    assert len(rows)==17
    for field in ('person','document','anchor'):
        assert rows['judged_'+field][:4]==[False]*4
        assert rows['possible_'+field][4:6]==[False,False]
    for field in ('document','anchor'):
        assert rows['contains_'+field][4:6]==[False,True]
    for name in ('about_document','about_subject','about_context','about_description','no_voice','no_speech','no_delegation'):
        assert rows[name][7:9]==[True,False]


def test_disjoint_judgment_and_possibility_scopes_can_both_have_witnesses(result):
    assert result['finite']['distinct_judgment_and_possibility_scopes']
    row=next(row for row in result['finite']['judgment_cases'] if row['selected']==[True,True] and
        row['endorsement']==[True,False] and not row['actual_endorsement'])
    assert row['results']==[False,True,False,True,True,False,False,True,True,False]


def test_missing_interpretations_are_not_filled_with_empty_or_false_values(result):
    assert result['finite']['unknown_relations_and_truth_refused']
    assert result['finite']['endorsement_does_not_evaluate_contained_truth']
    assert result['finite']['inner_message_truth_and_norms_not_executed']
    assert not result['finite']['certainty_degree_or_probability_measured']


def test_parent_notation_and_partial_source_scope_are_preserved(result):
    text,_=source_composed();doc=parse(text)
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    assert doc['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert doc['statements']==parent['statements']
    assert len(doc['declarations'])==len(parent['declarations'])+9
    assert result['new_primitives']==result['new_author_statements']==0
    assert result['finite']['standalone_agrees']
    assert not result['alignment']['semantic_completion']
    assert result['verified_full_units']=={'kant-1784':0,'einstein-1905':0}
    assert result['roundtrips']
    assert result==json.loads(REPORT.read_text(encoding='utf-8'))
