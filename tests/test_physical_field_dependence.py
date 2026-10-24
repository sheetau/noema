from scripts.check_physical_field_dependence import realization_checks,geometry_checks,pair_checks,presence_checks,binding_checks,presentation_checks,structure_checks

def test_realization():assert realization_checks()['same_process_two_physical_field_kinds']
def test_geometry():assert geometry_checks()['nonzero_arbitrary_direction_relative_motion']
def test_pair():assert pair_checks()['same_event_inverse_fields_and_region_bound']
def test_presence():assert presence_checks()['native_electric_and_magnetic_zero_nonzero_witnesses']
def test_binding():assert binding_checks()['every_witness_and_three_free_slots_distinguished']
def test_presentation():assert presentation_checks()['same_developed_theory_project_document_and_scope']
def test_structure():assert structure_checks()['whole_unit_review_not_yet_added']
