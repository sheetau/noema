from scripts.check_origin_clock_time import time_checks,scope_checks,presentation_checks,structure_checks

def test_proportional_and_difference_time():assert time_checks()['native_proportional_and_difference_equalities']
def test_all_current_clock_pairs():assert scope_checks()['native_time_formulas_on_all_selected_pairs']
def test_author_consequence():assert presentation_checks()['same_preceding_equations_and_derived_content']
def test_source_and_preserved_judgments():assert structure_checks()['prior_whole_unit_judgments_preserved']
