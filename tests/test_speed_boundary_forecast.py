from scripts.check_speed_boundary_forecast import equation_checks,caveat_checks,endpoint_checks,permission_checks,role_checks,presentation_checks,structure_checks

def test_same_equation_family():assert equation_checks()['same_event_all_records_and_unit_phi']
def test_application_not_just_numeric_failure():assert caveat_checks()['numerical_failure_and_physical_inapplicability_separate']
def test_unattained_endpoint_role():assert endpoint_checks()['nonempty_approachable_unattained_endpoint']
def test_physical_permission_and_actual_histories():assert permission_checks()['physical_permission_and_same_complete_membership_required']
def test_theory_and_all_eligible_objects():assert role_checks()['all_eligible_bodies_under_same_theory']
def test_same_view_and_quoted_forecast():assert presentation_checks()['same_view_for_caveat_and_forecast']
def test_source_and_preserved_evidence():assert structure_checks()['prior_whole_unit_judgments_preserved']
