from scripts import check_experimental_relation_tests as check

def test_independent_measurement_and_comparison():assert check.comparison_checks()
def test_potential_mass_and_charge_quantities():assert check.quantity_checks()
def test_geometric_radius_without_magnetic_formula():assert check.geometric_checks()
def test_physical_premises_do_not_assume_the_answer():assert check.premise_checks()
def test_all_existential_bindings_and_unknown_domains():assert check.possibility_checks()
def test_current_cases_and_three_access_conditions():assert check.connection_checks()
def test_preserved_source_and_meanings():assert check.structure_checks()
