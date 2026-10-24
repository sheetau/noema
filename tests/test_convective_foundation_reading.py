from scripts.check_convective_foundation_reading import physical_checks,global_checks,witness_checks,naming_checks,foundation_checks,structure_checks

def test_units_and_local_values():assert physical_checks()['same_local_density_charge_velocity_fields_and_jets']
def test_hypothesis_separate_from_laws():assert global_checks()['interpretation_does_not_require_equation_truth']
def test_all_witness_slots():assert witness_checks()['all_eight_physical_and_two_jet_slots_checked']
def test_historical_names_and_signed_charge():assert naming_checks()['nonzero_portion_not_net_charge_required']
def test_conditional_basis_of_same_theory():assert foundation_checks()['quoted_physics_not_executed']
def test_preservation():assert structure_checks()['equations_absent_from_entire_hypothesis_dependency_closure']
