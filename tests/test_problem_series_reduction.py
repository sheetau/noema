from scripts.check_problem_series_reduction import sequence_checks,reconstruction_checks,binding_checks,method_checks,structure_checks

def test_ordered_native_questions():assert sequence_checks()['native_questions_and_answers']
def test_reconstruction_and_unbounded_scope():assert reconstruction_checks()['native_unbounded_sequence_quantification_refused']
def test_shared_quantified_witnesses():assert binding_checks()['plan_and_solution_require_same_target_sequence']
def test_method_and_entire_problem_class():assert method_checks()['nonempty_entire_source_scope_required']
def test_preserved_previous_evidence():assert structure_checks()['all_406_previous_statements_and_meanings_preserved']
