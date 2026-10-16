import pytest
from scripts import check_unreceived_reference as check


@pytest.fixture(scope='module')
def generic():return check.generic_checks()


@pytest.fixture(scope='module')
def source():return check.source_checks()


def test_not_yet_includes_past_and_present_but_not_future_or_another_branch(generic):
    assert generic['event_patterns']==16
    assert generic['future_and_other_branch_do_not_affect_truth']


def test_empty_missing_anchor_and_invalid_orders_cannot_hide_receipt(generic):
    assert len(generic['invalid_histories'])==5
    assert all(v==[False] for v in generic['invalid_histories'].values())


def test_unknown_past_is_not_inferred_as_nonreceipt(generic):
    assert generic['unknown_past_and_anchor_refused']


def test_unknown_future_has_an_explicit_eager_interpreter_limit(generic):
    assert generic['unknown_future_diagnostic_skipped'] and generic['unknown_future_eager_refused']


def test_cited_answer_author_question_and_medium_are_kept_together(source):
    rows=source['contrasts']
    assert rows['baseline']==[True,True]
    assert rows['other_cited_document']==[False,True]
    assert rows['other_question']==[False,True]


def test_receiving_an_announcement_is_not_receiving_the_answer(source):
    assert source['contrasts']['received_other_item']==[True,True]


def test_prior_receipt_is_not_erased_by_current_nonpossession(source):
    assert source['contrasts']['received_past']==[True,False]
    assert source['contrasts']['received_now']==[True,False]


def test_other_person_context_and_future_do_not_supply_past_receipt(source):
    for variant in ('received_future','received_other_branch','received_other_person','received_other_context'):
        assert source['contrasts'][variant]==[True,True]


def test_existing_manuscript_and_temporal_contracts_are_preserved():
    assert check.structure()['previous_statements_preserved']==18


def test_only_two_explicit_footnote_ranges_are_claimed():
    rows=check.alignment()['segments']
    assert len(rows)==2 and rows[0]['source'].startswith('worin')
    assert rows[1]['source']=='Mir ist sie noch nicht zu Händen gekommen;'
