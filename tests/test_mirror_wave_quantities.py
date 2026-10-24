from scripts.check_mirror_wave_quantities import binding_checks,equation_checks,literal_angle_checks,quantifier_checks,presentation_checks,structure_checks

def test_binding():assert binding_checks()['all_82_roles_and_same_boolean_side_shared']
def test_equations():assert equation_checks()['all_six_printed_equalities_distinguished']
def test_literal_angle():assert literal_angle_checks()['inherited_line_angle_not_silently_changed_to_axis']
def test_quantifiers():assert quantifier_checks()['all_78_setting_quantifiers_and_76_witnesses_per_name_bound']
def test_presentation():assert presentation_checks()['attributed_false_angle_claim_not_executed_as_truth']
def test_structure():assert structure_checks()['all_396_previous_statements_and_meanings_preserved']
