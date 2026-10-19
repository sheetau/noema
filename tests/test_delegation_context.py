from scripts.check_delegation_context import scope_checks, ordinary_checks, attribution_checks, integrity_checks


def test_same_person_goal_and_hypothetical_scope_are_preserved():
    assert len(scope_checks()['contrasts']) == 16


def test_selected_results_are_not_all_possible_results():
    assert ordinary_checks()['unknown_inputs_refused'] == 3


def test_context_does_not_turn_presentation_into_actual_effort_facts():
    assert attribution_checks()['all_effort_facts_unknown']


def test_reading_is_bound_to_the_current_manuscript():
    assert integrity_checks()['current_selection_bound']
