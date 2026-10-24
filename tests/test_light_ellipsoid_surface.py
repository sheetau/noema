from scripts.check_light_ellipsoid_surface import affine_checks,geometry_checks,quantifier_checks,polynomial_checks,presentation_checks,structure_checks

def test_affine():assert affine_checks()['both_inverse_orders_all_three_components']
def test_geometry():assert geometry_checks()['all_time_centers_and_inverse_lorentz_surface_checked']
def test_quantifiers():assert quantifier_checks()['all_63_context_roles_bound']
def test_polynomial():assert polynomial_checks()['rational_polynomial_only']
def test_presentation():assert presentation_checks()['claim_colon_display_and_back_reference_preserved']
def test_structure():assert structure_checks()['all_390_statements_and_judgments_preserved']
