from scripts.check_field_symmetry_conclusion import premise_checks,probe_checks,coefficient_checks,final_field_checks,presentation_checks,structure_checks

def test_premises():assert premise_checks()['nonempty_necessity_and_all_premises']
def test_probe():assert probe_checks()['native_same_point_five_zeros_nonzero_N_and_signed_response']
def test_coefficient():assert coefficient_checks()['negative_branch_not_removed']
def test_final_fields():assert final_field_checks()['full_function_domain_refused']
def test_presentation():assert presentation_checks()['footnote_number_target_direction_and_author']
def test_structure():assert structure_checks()['negative_branch_and_same_old_event_checks_preserved']
