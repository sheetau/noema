from scripts.check_practical_time_convention import comparison_checks,quantifier_checks,content_checks,presentation_checks,structure_checks

def test_common_degrees_and_strong_comparison():assert comparison_checks()['native_existential_comparison_executed']
def test_quantified_degree_binding():assert quantifier_checks()['two_degree_witnesses_share_one_pair']
def test_same_rule_and_reasoning():assert content_checks()['native_comparison_inside_content']
def test_forward_reference_and_attribution():assert presentation_checks()['attribution_does_not_execute_following_argument']
def test_preserved_manuscript_and_readings():assert structure_checks()['prior_sentence_bindings_preserved']
