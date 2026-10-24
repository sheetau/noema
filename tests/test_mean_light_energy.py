from scripts.check_mean_light_energy import phase_checks,spatial_checks,physical_checks,integral_checks,setting_checks,ratio_checks,polynomial_checks,structure_checks

def test_phase():assert phase_checks()['instantaneous_value_not_used_as_mean']
def test_spatial():assert spatial_checks()['three_universal_slots_each_tested']
def test_physical():assert physical_checks()['all_29_roles_shared']
def test_integral():assert integral_checks()['same_weighted_and_unweighted_spatial_integrals']
def test_setting():assert setting_checks()['all_70_roles_shared']
def test_ratio():assert ratio_checks()['actual_lorentz_volume_law_not_assumed']
def test_polynomial():assert len(polynomial_checks()['lemmas'])==3
def test_structure():assert structure_checks()['all_386_statements_and_judgments_preserved']
