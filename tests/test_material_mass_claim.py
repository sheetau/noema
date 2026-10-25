from scripts.check_material_mass_claim import mass_checks,history_checks,charge_checks,presentation_checks,binding_checks,structure_checks

def test_charge_free_mass_setting():assert mass_checks()
def test_same_actual_histories_and_frames():assert history_checks()
def test_possible_addition_not_replacement_or_cancellation():assert charge_checks()
def test_reason_and_author_defined_electron():assert presentation_checks()
def test_shared_existential_roles_and_universal_bounds():assert binding_checks()
def test_preserved_evidence_and_structure():assert structure_checks()
