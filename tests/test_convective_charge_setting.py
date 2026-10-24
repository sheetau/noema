from scripts.check_convective_charge_setting import local_checks,amount_checks,carrier_checks,regional_checks,structure_checks

def test_local_equation_and_density_roles():assert local_checks()['same_charge_units_point_fields_and_all_velocity_components']
def test_physical_regional_totals():assert amount_checks()['all_regional_totals_have_physical_charge_kind_and_same_time_units']
def test_all_material_carriers():assert carrier_checks()['all_carriers_and_entire_charted_history_checked']
def test_regional_binding():assert regional_checks()['all_nine_shared_witness_positions_checked']
def test_preserved_evidence():assert structure_checks()['all_408_assertions_and_meanings_preserved']
