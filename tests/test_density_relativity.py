from scripts.check_density_relativity import model_checks,quantifier_checks,presentation_checks,reading_checks,structure_checks

def test_models():assert model_checks()['new_density_adoption_not_assumed_in_premise']
def test_quantifiers():assert quantifier_checks()['infinite_real_function_domains_refused']
def test_presentation():assert presentation_checks()['must_follow_direction_retained']
def test_reading():assert reading_checks()['first_sentence_complete_under_explicit_reading']
def test_structure():assert structure_checks()['conclusion_adoption_excluded_from_premise']
