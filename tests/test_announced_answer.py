import pytest
from scripts import check_announced_answer as check


@pytest.fixture(scope='module')
def result():return check.checks()


def test_citation_alone_does_not_locate_an_answer_in_the_announced_issue(result):
    rows=result['old_accepts_seven_missing_or_misbound_memberships']
    assert len(rows)==8
    assert rows['baseline']==dict(before=[True],after=[True])
    assert all(row==dict(before=[True],after=[False]) for name,row in rows.items() if name!='baseline')


def test_unknown_membership_remains_unknown(result):assert result['unknown_membership_refused']


def test_existing_reading_and_date_constraints_still_apply(result):assert len(result['preserved_contrasts'])==24


def test_containment_does_not_turn_into_receipt_or_reading_the_answer(result):
    rows=result['citation_nonreceipt_reading']
    assert rows['baseline/baseline']==[True,True,True]
    assert rows['baseline/received_past']==[True,False,True]
    assert rows['read_answer/baseline']==[True,True,False]


def test_only_one_definition_changes_and_reviewed_units_are_preserved():
    r=check.structure()
    assert r['changed_definitions']==['hzkk'] and r['new_declarations']==r['new_primitives']==0
    assert r['statements']==23 and r['reviewed_unit_meanings_preserved']
