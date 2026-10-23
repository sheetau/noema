"""Reject different scales even when both values and placements are valid."""
from fractions import Fraction
from scripts.check_reception_position_dependence import setup,run,relation,CASE,PAIR


def test_shared_unit_is_required_independently_of_value_difference():
    _,model,_,_,fields,_,candidates=setup(9,12)
    granted=model|{'eikk':relation({tuple(CASE),tuple(['right']+CASE[1:])})}
    assert run('eikl',PAIR,granted,'pair')
    original=fields['right','now']
    fields['right','now']=original[:-1]+('other',)
    # Retain the unequal value; rejection must not come from accidental equality.
    candidates['record2','clock','other','possible']=Fraction(12)
    assert not run('eikl',PAIR,granted,'pair')
    fields['right','now']=original
    assert run('eikl',PAIR,granted,'pair')
