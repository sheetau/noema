from scripts.check_contextual_motto import directive_checks,presentation_checks,integrated_conditions,structure


def test_courageous_undertaking_uses_the_author_gloss_without_success_or_competence():
    result=directive_checks()
    assert result['combinations']==32 and result['unknown_inputs_refused']==4


def test_two_quoted_directives_and_the_motto_remain_bound_to_the_same_passage():
    assert len(presentation_checks()['cases'])==10


def test_current_capacity_cause_and_imputation_have_the_adopted_conditional_scope():
    assert integrated_conditions()['combinations']==16


def test_the_old_competence_test_is_removed_from_active_meaning_not_merely_hidden():
    assert structure()['old_competence_test_absent_from_active_opening']
