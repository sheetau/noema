from scripts.check_defined_thoughts import checks


def test_existing_thought_interface_accepts_definition_expansion_and_refuses_unknowns():
    result = checks()
    assert result['cases']['baseline'] == [False, True, True]
    assert result['unresolved_inputs'] == ['different_polarity', 'unknown_criterion']
