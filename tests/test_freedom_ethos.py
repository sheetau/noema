from scripts import check_freedom_ethos as check

def test_exact_governed_group():check.scope_checks()
def test_all_clerical_contexts_and_same_comparisons():check.clerical_checks()
def test_all_others_with_same_unrestricted_condition():check.other_checks()
def test_same_context_and_point_for_all_liberties():check.policy_checks()
def test_support_preserves_content_without_executing_it():check.attitude_checks()
def test_inheritance_and_roundtrips():check.structure_checks()
