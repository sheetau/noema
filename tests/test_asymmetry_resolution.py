from scripts.check_asymmetry_resolution import classification_checks,physical_binding_checks,projection_checks,scope_checks,presentation_checks,structure_checks

def test_classifications():assert classification_checks()['all_allowed_accounts_have_common_mechanism']
def test_physical_binding():assert physical_binding_checks()['all_78_typed_arguments_and_physical_components_bound']
def test_projection():assert projection_checks()['every_witness_and_all_nine_free_keys_distinguished']
def test_scope():assert scope_checks()['same_introductory_objects_and_current_theory']
def test_presentation():assert presentation_checks()['introduction_reference_ferner_klar_and_author_preserved']
def test_structure():assert structure_checks()['old_360_statements_preserved']
