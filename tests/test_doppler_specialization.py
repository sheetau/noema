from scripts.check_doppler_specialization import numeric_checks,lift_checks,region_checks,condition_checks,universal_checks,presentation_checks,structure_checks

def test_printed_ratio_and_domain():assert numeric_checks()['cases']>200
def test_all_physical_speed_dependencies():assert lift_checks()['lifted_definitions']==12
def test_inverse_region_with_variable_speed():assert region_checks()['cases']==72
def test_zero_angle_and_same_settings():assert condition_checks()['all_60_setting_roles_bound']
def test_every_quantifier_in_all_three_forms():assert universal_checks()['quantified_slots_per_content']==56
def test_name_clear_form_and_attribution():assert presentation_checks()['no_quoted_physical_law_evaluated_by_attribution']
def test_inherited_evidence_and_script():assert structure_checks()['old_372_statements_and_judgments_preserved']
