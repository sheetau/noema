from scripts.check_local_times_only import stage_checks,method_checks,task_checks,binding_checks,content_checks,presentation_checks,structure_checks


def test_definition_stage_and_shared_time():assert stage_checks()['no_current_definition_not_eternal_nonexistence']
def test_all_prerequisites_and_success_conditions():assert method_checks()['successful_existing_method_refutes_inability']
def test_same_events_places_and_tasks():assert task_checks()['every_event_and_scope_slot_checked']
def test_previous_local_rule_bindings():assert binding_checks()['all_local_rule_roles_bound_to_prior_eik4']
def test_clauses_and_explanatory_reason():assert content_checks()['semicolon_reason_has_correct_direction']
def test_attribution_contrasts_and_names():assert presentation_checks()['both_contrasts_designations_author_and_order_preserved']
def test_source_and_previous_judgments():assert structure_checks()['both_prior_sentence_bindings_preserved']
