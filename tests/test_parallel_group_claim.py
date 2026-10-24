from scripts.check_parallel_group_claim import necessity_checks,group_checks,presentation_checks,structure_checks

def test_necessity():assert necessity_checks()['candidates_selected_only_by_premise']
def test_group():assert group_checks()['whole_real_family_and_function_domain_not_finitely_enumerated']
def test_presentation():assert presentation_checks()['parenthetical_necessity_targets_same_group']
def test_structure():assert structure_checks()['necessity_premise_does_not_depend_on_conclusion']
