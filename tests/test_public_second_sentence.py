from scripts import check_public_second_sentence as checks


def test_metaphor_target_uses_the_actual_origin_and_departure_witnesses():
    assert checks.binding_checks()['wrong_role_mutations_refused'] == 7


def test_self_achievement_and_precedence_are_distinct():
    assert checks.achievement_checks()['existential_achievement_alone_does_not_prove_first_send_order']


def test_complete_sentence_keeps_claim_background_metaphor_reason_and_tone():
    assert checks.attribution_checks()['attribution_combinations'] == 32


def test_evaluative_naming_relation_is_not_specific_to_this_word_or_work():
    assert checks.portability_checks()['no_kant_or_crowd_symbols_needed']


def test_review_covers_every_clause_and_preserves_existing_judgments():
    assert checks.structure_checks()['reviewed_second_sentence_characters'] == 274
