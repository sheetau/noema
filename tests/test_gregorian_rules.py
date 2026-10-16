import pytest
from scripts import check_gregorian_rules as check


def test_digit_integrality_and_quotient_remainder_certificates():
    r=check.numeral_checks()
    assert r['valid_digits']==32 and r['value_1784_checked']


def test_full_400_year_cycle_and_century_boundaries():
    r=check.leap_checks()
    assert r['years']==400 and r['leap_count']==97
    assert r['boundary_cases']['1900']==[False] and r['boundary_cases']['2000']==[True]


def test_all_months_in_four_year_types_and_invalid_labels():
    r=check.date_checks()
    assert r['month_day_cases']==432 and r['zero_year_refused']


def test_invalid_proofs_cannot_be_treated_as_common_years():
    r=check.corruption_checks()
    assert r['invalid_digit_certificates']==28 and r['invalid_certificate_not_a_common_year']


def test_source_dates_share_the_same_explicit_year_certificate():
    r=check.source_checks()
    assert r['contrasts']['baseline']==[True] and r['historical_calendar_not_identified']


def test_no_leap_year_or_integer_or_modulo_primitive_was_added():
    r=check.structure()
    assert r['new_primitives']==0 and r['new_definitions']==8


def test_new_conditions_do_not_expand_source_range():
    assert len(check.alignment()['segments'])==2
