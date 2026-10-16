from fractions import Fraction
import pytest
from scripts import check_calendar_dateline as check


@pytest.fixture(scope='module')
def checked():
    return check.checks()


def test_calendar_year_month_day_and_context_are_bound(checked):
    rows=checked['source_contrasts']
    assert rows['baseline']==[True]
    assert all(value==[False] for name,value in rows.items() if name!='baseline')


def test_fractional_negative_and_out_of_range_positions_are_rejected(checked):
    assert len(checked['positions'])==8
    assert [row['result'] for row in checked['positions']]==[True]+[False]*7


def test_adjacent_date_remains_expressible(checked):
    assert checked['adjacent_date_expressible']


def test_unknown_calendar_and_display_relations_are_not_invented(checked):
    assert len(checked['unknown_inputs_refused'])==5


def test_previous_manuscript_and_name_annotations_are_preserved():
    assert check.structure()['previous_statements_preserved']==17


def test_source_date_has_not_been_replaced_by_publication_date():
    assert '1784' in check.source_unit()['text']
    doc=check.source_document()
    assert {d['name'] for d in doc['declarations']}=={
        'dg','hzih','hzik',*check.PRIMITIVES,'rqrm','hzje'}


def test_nonstandard_month_lengths_are_supported():
    # The address relation does not prescribe 12 months or 30 days universally.
    doc=check.date_fixture(0,0);values=check.model(doc)
    values.update(jday=lambda:'day0',hzjg=lambda:'month0',
        hzis=lambda *args:check.SequenceValue(('month0',),'"individual"'),
        hzit=lambda *args:check.SequenceValue(('day0',),'"individual"'))
    assert check.evaluate(doc,values)==[True]
