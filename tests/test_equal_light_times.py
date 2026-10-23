from scripts.check_equal_light_times import duration_checks,opposite_checks,scope_checks,adoption_checks,presentation_checks,structure_checks


def test_light_travel_duration():assert duration_checks()['elapsed_time_is_nonnegative_difference']
def test_opposite_directions_and_equal_durations():assert opposite_checks()['numerical_durations_not_endpoint_times_compared']
def test_complete_comparison_scope():assert scope_checks()['all_corresponding_pairs_checked']
def test_possible_definition_not_actual_measurement():assert adoption_checks()['rule_adopted_as_definition_not_measured_fact']
def test_latter_time_and_author_presentation():assert presentation_checks()['latter_common_time_anaphora_author_and_order_preserved']
def test_source_and_preserved_judgments():assert structure_checks()['three_prior_sentence_bindings_preserved']
