from scripts.check_thinking_disseminators import group_checks,future_checks,individual_checks,composite_checks,unknown_checks,structure


def test_appointment_membership_and_joint_condition_bind_the_same_people():
    assert group_checks()['membership_appointment_and_joint_condition_combinations']==64


def test_each_future_opportunity_can_have_different_people():
    assert future_checks()['different_people_at_different_points_allowed']


def test_the_thinker_and_transmitter_are_the_same_person():
    assert individual_checks()['split_thinkers_and_transmitters']==[False,False]


def test_two_native_appointed_thinkers_depart_and_transmit_the_concrete_profile():
    result=composite_checks()
    assert result['group_evaluated_without_lowering_or_replacement']
    assert result['future_uses_explicit_short_circuit_diagnostic']


def test_unknown_appointments_judgments_and_assent_are_not_false():
    assert unknown_checks()['unknown_inputs_refused']==7


def test_existing_meanings_and_review_bindings_remain_intact():
    assert structure()['new_primitives']==0
