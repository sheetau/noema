from scripts import check_civic_peace_concord as check


def test_public_disturbance_requires_same_actual_episode():check.peace_checks()
def test_concord_is_not_unanimous_opinion_or_absence_of_violence():check.concord_checks()
def test_harm_to_either_public_good_counts():check.harm_checks()
def test_no_warranted_threat_requires_nonempty_assessed_condition():check.threat_checks()
def test_same_liberty_frame_and_assessment_feed_both_harms():check.liberty_binding_checks()
def test_existing_meanings_and_notations_preserved():check.structure_checks()
