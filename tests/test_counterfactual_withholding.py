import pytest
from scripts import check_counterfactual_withholding as check


@pytest.fixture(scope='module')
def source():return check.source_checks()


def test_receipt_and_nonreceipt_complement_only_on_valid_histories():
    rows=check.prefix_checks()
    assert rows['event_patterns']==16
    assert all(x==[False,False] for x in rows['invalid_histories'].values())


def test_counterfactual_requires_nonempty_selected_worlds_with_both_parts():
    assert check.conditional_checks()['truth_combinations']==128


def test_actual_nonreceipt_is_connected_to_the_previous_statement(source):
    assert source['contrasts']['baseline']==[True]
    assert source['contrasts']['different_selected_anchor']==[True]
    for v in ('actually_received','wrong_actual_frame','wrong_actual_anchor','empty_actual_history'):
        assert source['contrasts'][v]==[False]


def test_empty_or_antecedent_false_selection_cannot_pass(source):
    for v in ('empty_selection','selected_without_receipt','invalid_selected_anchor'):
        assert source['contrasts'][v]==[False]


def test_antecedent_and_result_cannot_come_from_different_worlds(source):
    assert source['contrasts']['split_worlds']==source['contrasts']['second_bad_outcome']==[False]


def test_prior_and_present_documents_and_the_causal_action_are_bound(source):
    for v in ('same_documents','other_received_item','other_withheld_document','other_cause_document','other_cause_action','no_influence'):
        assert source['contrasts'][v]==[False]


def test_quoted_antecedent_viewpoint_and_actual_context_reach_the_selector(source):
    assert source['antecedent_description_preserved']
    for v in ('other_antecedent_description','other_viewpoint','other_actual_context'):
        assert source['contrasts'][v]==[False]


def test_actual_consequent_is_not_asserted(source):
    assert source['contrasts']['actual_withholding']==source['contrasts']['baseline']==[True]


def test_unknown_selection_history_and_result_are_not_filled_in(source):
    assert source['unknown_inputs_refused'] and source['stored_graph_uncached_comparisons']==4


def test_parent_text_and_names_are_preserved():
    assert check.structure()['previous_statements_preserved']==21


def test_alignment_stops_before_the_exploratory_presentation():
    row=check.alignment()['segments'][0]
    assert row['source']=='sonst würde sie die gegenwärtige zurükgehalten haben,'
