from scripts.check_clock_definition_proposal import clock_checks,proposal_checks,difficulty_checks,modality_checks,presentation_checks,structure_checks

def test_same_clock_and_hand_reading():assert clock_checks()
def test_definition_rule_and_reference():assert proposal_checks()
def test_all_difficulties_and_single_result():assert difficulty_checks()
def test_tentative_nonfactive_scope():assert modality_checks()
def test_attribution_and_main_text_order():assert presentation_checks()
def test_source_and_prior_bindings():assert structure_checks()
