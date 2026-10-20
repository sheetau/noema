from scripts.check_clerical_audiences import role_checks, pupil_checks, audience_checks, unknown_checks, structure_checks


def test_clerical_conditions_share_the_identified_role_and_institution(): role_checks()


def test_own_pupils_share_the_introductory_religious_question_answer_course(): pupil_checks()


def test_both_recipient_ranges_are_complete_and_may_overlap(): audience_checks()


def test_unknown_institutional_and_recipient_inputs_are_rejected(): unknown_checks()


def test_preserved_meanings_archived_evidence_and_roundtrips(): structure_checks()
