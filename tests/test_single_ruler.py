from scripts import check_single_ruler as checks


def test_ruler_is_same_appointed_holder_of_the_highest_political_role():
    assert checks.role_checks()['native_hzfn_rm2_rex_and_same_institution']


def test_world_scope_binds_the_same_person_and_community():
    assert checks.world_checks()['same_person_community_reference_and_point']


def test_ranked_messages_use_the_speaker_as_the_norm_source_for_every_recipient():
    assert checks.speech_checks()['same_speaker_is_both_norm_sources']


def test_uniqueness_counts_qualified_speakers_not_rulers_or_events():
    assert checks.uniqueness_checks()['exactly_one_qualified_speaker_not_one_ruler_or_one_call']


def test_aside_contrast_and_attribution_keep_world_content_quoted():
    assert checks.discourse_checks()['world_and_quoted_reference_not_executed']


def test_parenthetical_sentence_review_preserves_previous_judgments():
    assert checks.structure_checks()['new_reviewed_sentence_characters'] == 91
