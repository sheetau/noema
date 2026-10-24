from scripts.check_auxiliary_role import designation_checks,role_checks,explanation_checks,presentation_checks,structure_checks

def test_designation():assert designation_checks()['same_expression_physical_role_concept_and_theory_introduction']
def test_role():assert role_checks()['nonempty_all_uses_not_just_one_success']
def test_explanation():assert explanation_checks()['same_concept_through_role_and_introduction_reason']
def test_presentation():assert presentation_checks()['author_man_sieht_and_same_whole_content_bound']
def test_structure():assert structure_checks()['other_358_statements_preserved']
