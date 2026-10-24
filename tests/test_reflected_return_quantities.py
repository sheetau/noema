from scripts.check_reflected_return_quantities import binding_checks,equation_checks,disagreement_checks,quantifier_checks,presentation_checks,structure_checks

def test_same_inverse_setting():assert binding_checks()['all_90_roles_bound']
def test_six_equalities():assert equation_checks()['all_three_rows_and_six_equalities_checked']
def test_disagreements_kept():assert disagreement_checks()['normal_incidence_printed_disagreement']
def test_quantifiers():assert quantifier_checks()['boolean_side_and_infinite_domain_preserved']
def test_discourse():assert presentation_checks()['finally_scoped_to_same_three_stage_series']
def test_preservation():assert structure_checks()['all_400_previous_statements_and_meanings_preserved']
