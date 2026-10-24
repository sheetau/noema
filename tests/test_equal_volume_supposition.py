from scripts.check_equal_volume_supposition import background_checks,comparison_checks,quantifier_checks,presentation_checks,reading_checks,structure_checks

def test_background():assert background_checks()['all_70_physical_roles_shared']
def test_comparison():assert comparison_checks()['comparison_nonempty_when_actual_volumes_differ']
def test_quantifiers():assert quantifier_checks()['all_65_or_66_roles_bound_same_in_premise_and_conclusion']
def test_presentation():assert presentation_checks()['hypothetical_construction_not_actual_volume_claim']
def test_reading():assert reading_checks()['first_and_second_sentences_prose_characters']==301
def test_structure():assert structure_checks()['all_386_statements_and_judgments_preserved']
