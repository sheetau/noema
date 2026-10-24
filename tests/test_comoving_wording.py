from scripts.check_comoving_wording import boost_checks,field_checks,physical_checks,quantifier_checks,presentation_checks,structure_checks

def test_boost():assert boost_checks()['native_inverse_and_spacetime_interval']
def test_field():assert field_checks()['both_fields_mixed_and_inverse_coordinates_evaluated']
def test_physical():assert physical_checks()['whole_frame_motion_and_physical_chart_correspondence']
def test_quantifier():assert quantifier_checks()['every_witness_and_free_slot_distinguished']
def test_presentation():assert presentation_checks()['same_author_order_second_item_and_new_wording']
def test_structure():assert structure_checks()['semantic_judgment_separate']
