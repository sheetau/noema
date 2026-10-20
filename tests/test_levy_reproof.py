from scripts.check_levy_reproof import (
    message_checks,reproof_checks,standing_checks,case_checks,unknown_checks,structure_checks)


def test_assertive_message_can_have_false_content():
    message_checks()


def test_reproof_is_same_event_and_subject_for_every_fixed_recipient():
    reproof_checks()


def test_self_taken_standing_and_failed_criteria_share_actor_and_point():
    standing_checks()


def test_same_levy_is_required_at_reference_and_criticism_point():
    case_checks()


def test_unknown_inputs_and_unknown_criterion_are_rejected():
    unknown_checks()


def test_preserved_meanings_lexical_evidence_and_roundtrips():
    structure_checks()
