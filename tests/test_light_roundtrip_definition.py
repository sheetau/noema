from scripts.check_light_roundtrip_definition import physical_checks,equation_checks,scope_checks,hypothetical_checks,presentation_checks,structure_checks


def test_same_light_and_three_clock_readings():assert physical_checks()['same_ray_reflection_and_A_B_A_readings']
def test_exact_synchrony_equation():assert equation_checks()['exact_two_differences_match_three_named_readings']
def test_all_relevant_trials():assert scope_checks()['single_success_and_empty_trials_insufficient']
def test_supposition_and_definition():assert hypothetical_checks()['supposition_does_not_assert_synchrony']
def test_explanation_and_source_order():assert presentation_checks()['two_native_presentations_and_local_names_checked']
def test_source_and_previous_judgments():assert structure_checks()['four_prior_sentence_bindings_preserved']
