import pytest
from scripts import check_dateline_reading as check


def test_calendar_and_period_conventions_change_without_expanding_text():
    result=check.structure()
    assert set(result['changed_meanings'])=={'hzix','hzjg','hzjh'}
    assert result['statements']==23 and result['additional_manuscript_characters']==0
    assert result['signature_dependency_meanings_preserved'] and result['identifiers_preserved']


@pytest.fixture(scope='module')
def source():return check.checks()


def test_wrong_referents_and_nonunique_dates_do_not_satisfy_the_current_dateline(source):
    assert len(source['contrasts'])==19
    assert source['contrasts']['baseline']==[True]
    assert all(value==[False] for name,value in source['contrasts'].items() if name!='baseline')


def test_unknown_assignments_are_not_false_facts_or_guessed_dates(source):
    assert set(source['unknown_inputs_refused'])=={'unknown_year','unknown_assignment','unknown_date','unknown_month_label','unknown_day_label'}
    assert source['historical_calendar_identification_proved_by_models'] is False
