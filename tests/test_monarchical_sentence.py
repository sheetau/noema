from scripts.check_monarchical_sentence import core_checks,adapter_checks,conditional_checks,discourse_checks,structure_checks

def test_both_halves_keep_the_fixed_reference():
    assert core_checks()['both_halves_and_fixed_reference']['(True, True)']==[True]*3

def test_comparison_and_grounding_share_exact_bindings():
    assert adapter_checks()['exact_lengths_reference_candidate_and_unknown_checked']

def test_conditional_denial_does_not_become_a_blanket_ban():
    assert conditional_checks()['all_monarchs_same_law_and_candidate_conditional']['no_people_denial']

def test_all_discourse_links_and_directions_without_executing_quotes():
    assert discourse_checks()['quoted_choices_prohibitions_wills_and_authority_not_executed']

def test_source_reading_roundtrips_and_prior_evidence_are_preserved():
    assert structure_checks()['new_reviewed_sentence_characters']==203
