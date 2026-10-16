import pytest
from scripts import check_dated_reading as check


@pytest.fixture(scope='module')
def source():return check.source_checks()


def test_reading_requires_occurrence_reader_text_and_carrier():
    assert check.generic_checks()['condition_combinations']==8


def test_reading_the_announcement_does_not_assert_reading_the_answer(source):
    assert source['contrasts']['baseline']==[True]
    assert source['contrasts']['read_answer']==[False]
    assert source['contrasts']['read_carrier']==[False]


def test_carrier_issue_and_announced_issue_are_bound_separately(source):
    for variant in ('other_carrier','other_announced_issue','wrong_issue_series','other_contained_text'):
        assert source['contrasts'][variant]==[False]


def test_day_thirteen_day_thirty_and_month_are_not_interchanged(source):
    for variant in ('wrong_issue_day','wrong_issue_month','wrong_day_number','other_month','other_year','other_calendar'):
        assert source['contrasts'][variant]==[False]


def test_same_day_does_not_force_same_instant(source):
    assert source['contrasts']['baseline']==source['contrasts']['same_instant']==[True]
    assert source['contrasts']['read_outside_today']==source['contrasts']['anchor_outside_today']==[False]


def test_names_issues_and_series_are_not_identified(source):
    assert source['contrasts']['name_is_series']==source['contrasts']['issue_is_series']==[False]
    assert source['contrasts']['names_on_read_act']==[False]


def test_unknown_reading_and_calendar_information_is_refused(source):
    assert source['unknown_inputs_refused']


def test_reading_coexists_with_nonreceipt_of_the_referenced_answer():
    rows=check.combined_checks()
    assert rows['baseline/baseline']==[True,True,True]
    assert rows['received_past/baseline']==[True,False,True]


def test_parent_statements_and_identifier_forms_are_preserved():
    assert check.structure()['previous_statements_preserved']==20


def test_source_range_stops_at_the_already_written_relative_clause():
    row=check.alignment()['segments'][0]
    assert row['source'].startswith('In den Büsching') and row['source'].endswith('von diesem Monat, ')
