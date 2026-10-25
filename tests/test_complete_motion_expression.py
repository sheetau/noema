from scripts import check_complete_motion_expression as check

def test_necessity_sufficiency_and_counterexamples():assert check.equivalence_checks()
def test_complete_physical_contents_and_applicability():assert check.physical_content_checks()
def test_every_universal_binding():assert check.binding_checks()
def test_specialization_to_the_previous_full_items():assert check.specialization_checks()
def test_same_theory_scope_and_background():assert check.theory_scope_checks()
def test_source_roles_and_references():assert check.presentation_checks()
def test_preserved_source_and_evidence():assert check.structure_checks()
