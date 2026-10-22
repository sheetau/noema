from scripts.check_royal_insight_reproof import maximum_checks,held_checks,reason_checks,authority_checks,reproof_checks,joining_checks,structure_checks

def test_maximum_uses_full_domain_and_allows_ties():
    assert maximum_checks()['native_full_range_maximum']['ties']

def test_self_assessment_does_not_execute_quoted_truth_or_rank():
    assert held_checks()['objective_false_content_allowed']

def test_same_held_view_is_reason_for_same_intervention():
    assert reason_checks()['ranking_judgment_alone_not_reason']

def test_office_does_not_confer_epistemic_superiority_in_literal_domain():
    assert authority_checks()['literal_grammar_domain_and_all_rulers']['nongrammar_exception']

def test_possible_justified_reproof_is_not_actual_criticism():
    assert reproof_checks()['actuality_not_required']

def test_same_activity_and_exact_content_bindings():
    assert len(joining_checks()['adapters']['r5p2']['independent_positions'])==7

def test_preserved_evidence_and_no_premature_semantic_credit():
    assert structure_checks()['verified_characters_added']==0
