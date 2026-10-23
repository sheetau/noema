from scripts.check_origin_clock_equations import numeric_checks,bridge_checks,scope_checks,presentation_checks,structure_checks

def test_both_native_equations():assert numeric_checks()['both_equations_native_and_independently_distinguished']
def test_same_clock_current_correspondence():assert bridge_checks()['three_origin_components_and_shared_event_required']
def test_all_current_clock_pairs():assert scope_checks()['native_equations_applied_to_each_selected_pair']
def test_author_obvious_equations():assert presentation_checks()['author_obviousness_conjunction_and_source_order']
def test_source_and_preserved_judgments():assert structure_checks()['prior_whole_unit_judgments_preserved']
