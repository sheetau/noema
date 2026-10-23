from scripts.check_clock_definition_scope import local_rule_checks,scope_checks,series_checks,adequacy_checks,equivalence_checks,conditional_checks,presentation_checks,structure_checks

def test_local_indication_and_target_coincidence():assert local_rule_checks()
def test_exclusive_local_and_remote_scope():assert scope_checks()
def test_all_members_of_different_series():assert series_checks()
def test_all_requirements_and_known_insufficiency():assert adequacy_checks()
def test_two_way_equivalence_of_tasks():assert equivalence_checks()
def test_conditions_on_same_definition():assert conditional_checks()
def test_actual_confirmation_contrast_and_insertion():assert presentation_checks()
def test_source_and_inherited_bindings():assert structure_checks()
