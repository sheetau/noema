from scripts import check_prescription_effects as checks


def test_applicability_and_nonfulfillment_match_existing_prescription_semantics():
    assert checks.truth_checks()['combinations'] == 64


def test_rule_issuer_target_and_unknown_inputs_are_kept_separate():
    assert checks.binding_checks()['issuer_distinct_from_rule_source']


def test_quoted_target_adapter_preserves_syntax_and_exact_binding_shape():
    assert checks.adapter_checks()['distinct_goal_descriptions_remain_distinct']


def test_opposing_contributions_do_not_assert_opposing_facts():
    assert checks.conflict_checks()['conflict_does_not_assert_both_goal_truths']


def test_application_changes_do_not_automatically_imply_legislative_changes():
    assert checks.transition_checks()['adoption_change_distinct_from_condition_change']


def test_notation_and_existing_meanings_are_preserved():
    assert checks.structure_checks()['roundtrips']
