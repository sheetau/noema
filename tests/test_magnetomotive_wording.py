from scripts.check_magnetomotive_wording import motion_checks,approximation_checks,force_checks,comoving_checks,quantifier_checks,presentation_checks,structure_checks

def test_motion():assert motion_checks()['same_pole_kind_unit_value_motion_and_point']
def test_approximation():assert approximation_checks()['negative_cross_product_all_directions']
def test_force():assert force_checks()['same_pole_static_dynamic_residual_and_three_records']
def test_comoving():assert comoving_checks()['same_new_amount_record_and_force']
def test_quantifiers():assert quantifier_checks()['every_old_new_witness_and_free_slot_checked']
def test_presentation():assert presentation_checks()['author_analogy_source_target_and_quoted_term']
def test_structure():assert structure_checks()['whole_unit_review_not_yet_added']
