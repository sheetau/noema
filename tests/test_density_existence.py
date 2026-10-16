from scripts import check_density_existence as check


def test_actual_density_equations_have_constructed_rational_outputs():
    result = check.proofs()
    assert result['existence']['status'] == 'valid'
    assert result['uniqueness']['status'] == 'valid'
    assert not result['physical_source_applicability_proved']


def test_denominator_and_velocity_sign_cannot_be_removed_or_changed():
    result = check.proofs()
    assert result['missing_denominator_condition']['status'] == 'uncertified'
    assert result['wrong_velocity_sign']['status'] == 'uncertified'


def test_zero_negative_density_and_negative_denominator_have_outputs():
    rows = check.concrete_cases()['cases']
    for name in ('zero_density_nonzero_velocity', 'negative_density', 'negative_denominator'):
        assert rows[name]['actual_senr_satisfied']
    assert rows['zero_density_nonzero_velocity']['outputs'][1] != '0'


def test_diagonal_entries_are_not_mistaken_for_unique_outputs():
    result = check.concrete_cases(); rows = result['cases']
    assert rows['positive_density']['outputs'][:4] == rows['different_diagonal_split']['outputs'][:4]
    assert rows['positive_density']['outputs'][4:] != rows['different_diagonal_split']['outputs'][4:]
    assert result['singular_denominator_refused']
