from scripts.check_human_vocation_offense import vocation_checks,progress_checks,offense_checks,binding_checks,conditional_checks,integrated_checks,structure_checks

def test_original_vocation_preserves_kind_origin_and_exact_content():
    r=vocation_checks();assert sum(r['native_vocation_contrasts'].values())==1 and r['progress_not_executed']

def test_progress_is_the_same_general_enlightenment_relation():
    r=progress_checks();assert sum(r['same_group_reference_history_and_ordered_points'].values())==1

def test_grave_offense_uses_same_norm_nature_and_undertaking():
    r=offense_checks();assert sum(r['same_norm_ground_conduct_and_protected_nature'].values())==1
    assert r['formation_and_goal_not_executed'] and r['unknown_rejected']

def test_six_target_adapters_preserve_positions_and_exact_length():
    r=binding_checks();assert all(len(m)==36 and sum(m)==6 for m in r['six_position_matrices'].values())

def test_hypothetical_not_actual_formation_and_all_candidates():
    r=conditional_checks();assert sum(r['conditional_truth_table'].values())==3 and len(r['all_candidate_oracle'])==16

def test_vocation_and_offense_are_connected_without_goal_execution():
    r=integrated_checks();assert sum(r['native_vocation_offense_and_condition'].values())==2
    assert r['relative_supplement_independent_of_agreement_existence'] and r['progress_and_success_not_evaluated']

def test_pinned_meanings_reports_and_100_assertions_are_preserved():
    r=structure_checks();assert (r['new_definitions'],r['new_primitives'],r['preserved_manuscript_statements'])==(7,6,100)
