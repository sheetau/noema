from scripts.check_confinement_depiction import target_checks,unknown_checks,confinement_checks,attribution_checks,structure


def test_same_person_is_selected_later_without_forcing_past_belief_or_current_nonattempt():
    assert target_checks()['cases']['baseline']==[True,False,True]


def test_unknown_supervision_attempt_cause_or_time_is_not_negative_evidence():
    assert unknown_checks()['unknown_inputs_refused']==4


def test_current_confinement_keeps_onset_and_continuity_separate():
    rows=confinement_checks()['cases']
    assert rows['released_middle']==[True,False,True]
    assert rows['already_confined']==[False,False,True]


def test_nonliteral_presentation_never_executes_either_described_world():
    assert attribution_checks()['target_and_depiction_inputs_unknown']


def test_connected_manuscript_preserves_existing_whole_unit_judgments():
    assert structure()['nine_review_bindings_preserved']
