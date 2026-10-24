from scripts.check_attached_material_charge import measure_checks,pullback_checks,binding_checks,fixed_checks,size_checks,structure_checks

def test_signed_material_portions():assert measure_checks()['native_all_subsets_of_two_labels_checked']
def test_spatial_inverse_images():assert pullback_checks()['same_material_label_all_four_coordinates']
def test_physical_charge_binding():assert binding_checks()['physical_material_and_spatial_amounts_share_all_references']
def test_unchanging_attachment():assert fixed_checks()['constant_total_with_internal_exchange_rejected']
def test_small_rigid_body():assert size_checks()['smallness_requires_prior_context_scale_and_rigidity']
def test_preservation():assert structure_checks()['all_408_statements_and_meanings_preserved']
