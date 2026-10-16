import pytest
from scripts import check_labeled_dates as check


@pytest.fixture(scope='module')
def source():return check.source_checks()


def test_assignments_and_uniqueness_for_all_three_calendar_levels():
    assert check.generic_checks()['combinations']==64


def test_dateline_and_footnote_share_label_semantics(source):
    assert source['contrasts']['hzje/baseline']==source['contrasts']['hzkk/baseline']==[True]


def test_wrong_labels_and_ambiguous_addresses_are_rejected(source):
    for root in ('hzje','hzkk'):
        for variant in ('wrong_month_label','wrong_day_label','ambiguous_month','ambiguous_day','ambiguous_year'):
            assert source['contrasts'][root+'/'+variant]==[False]


def test_calendar_parent_and_context_are_not_interchangeable(source):
    assert source['other_context_and_parent_refused']


def test_unknown_labels_are_not_guessed(source):
    assert source['unknown_labels_refused']


def test_missing_periods_do_not_renumber_remaining_dates():
    r=check.gap_checks()
    for row in r['synthetic_gap_contrasts'].values():assert row=={'old_offset':[False],'new_label':[True]}


def test_only_the_three_source_date_calls_change():
    r=check.structure()
    assert r['changed_definitions']==['hzje','hzkk'] and r['previous_statements_preserved']==23


def test_ranges_are_already_drafted():
    assert [r['unit'] for r in check.alignment()['segments']]==['kant-1784:u0019','kant-1784:u0020']
