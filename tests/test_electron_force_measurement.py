from scripts.check_electron_force_measurement import force_checks,calibration_checks,trial_checks,convention_checks,binding_checks,structure_checks

def test_same_physical_force():assert force_checks()
def test_calibrated_elastic_gauge():assert calibration_checks()
def test_possible_measurement_trials():assert trial_checks()
def test_mass_convention_and_candidates():assert convention_checks()
def test_shared_witnesses_and_question():assert binding_checks()
def test_preserved_structure():assert structure_checks()
