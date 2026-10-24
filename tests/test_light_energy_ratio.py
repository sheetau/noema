from scripts.check_light_energy_ratio import numeric_checks,physical_checks,binding_checks,polynomial_checks,presentation_checks,structure_checks

def test_numeric():assert numeric_checks()['both_equalities_and_middle_density_volume_products_preserved']
def test_physical():assert physical_checks()['same_two_weighted_and_unweighted_integrals_bound_to_70_roles']
def test_binding():assert binding_checks()['all_65_shared_context_roles_and_64_name_witnesses_checked']
def test_polynomial():assert polynomial_checks()['positive_root_branch_preserved']
def test_presentation():assert presentation_checks()['names_consequence_both_displays_relative_clause_and_strict_comparison_preserved']
def test_structure():assert structure_checks()['all_392_statements_and_judgments_preserved']
