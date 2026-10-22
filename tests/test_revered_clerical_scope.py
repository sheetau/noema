from scripts import check_revered_clerical_scope as check

def test_actual_regard_is_a_separate_state():check.attitude_checks()
def test_worthiness_requires_true_ground_and_all_nonempty_criteria():check.worthiness_checks()
def test_same_clerical_ground_names_and_response():check.bound_worthiness_checks()
def test_under_the_same_qualified_ruler():check.ruler_checks()
def test_same_political_and_clerical_scope():check.scope_checks()
def test_inheritance_roundtrips_and_quote_ranks():check.structure_checks()
