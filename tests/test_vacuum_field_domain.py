from scripts.check_vacuum_field_domain import point_checks,region_checks,field_checks,equation_checks,structure_checks


def test_material_absence():assert point_checks()['unknown_occupancy_rejected']
def test_entire_region():assert region_checks()['native_full_coordinate_domain_refused']
def test_physical_fields():assert field_checks()['nonzero_electric_and_magnetic_fields_allowed_in_vacuum']
def test_same_equations():assert equation_checks()['native_six_curl_balances_checked']
def test_preservation():assert structure_checks()['all_357_statements_and_prior_judgments_preserved']
