from scripts import check_uncertain_judgment as checks


def test_invalid_profile_is_not_unreliability():
    assert checks.profile_checks()['invalid_is_not_unreliable']


def test_actual_supported_judgment_and_unreliable_comparisons():
    assert checks.judgment_checks()['current_supported_judgment_can_be_unreliable']


def test_conditional_requires_same_person_and_a_nonvacuous_antecedent():
    assert checks.conditional_checks()['same_person_and_scope']


def test_native_departure_and_judgment_in_one_world():
    assert checks.native_conditional_checks()['native_antecedent_and_consequence_joint_execution']


def test_conditional_quotation_does_not_execute_its_content():
    assert checks.quotation_checks()['closed_conditional_quotable_without_world_evaluation']


def test_existing_judgments_and_reversible_notations_are_preserved():
    assert checks.structure_checks()['candidate_not_asserted']
