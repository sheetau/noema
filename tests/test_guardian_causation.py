from scripts.check_guardian_causation import causal_checks, majority_checks, source_checks, specialization_checks, attribution_checks, structure


def test_actual_causation_is_not_explanatory_adoption():
    assert len(causal_checks()['combinations']) == 16


def test_majority_takes_a_property_and_keeps_strict_degree_and_population_checks():
    assert len(majority_checks()['combinations']) == 64


def test_guardians_cause_judgment_without_asserting_actual_danger_or_causing_burden():
    result = source_checks()['contrasts']
    assert result['no_causation'][4:6] == [False, True]
    assert result['no_adoption'][4:6] == [True, False]


def test_previous_joint_property_is_preserved_as_a_specialization():
    assert specialization_checks()['previous_joint_predicate_reproduced']


def test_author_attribution_does_not_execute_causal_or_gender_claims():
    assert attribution_checks()['causal_burden_judgment_and_gender_facts_unknown']


def test_old_meanings_and_reviewed_sentences_are_preserved():
    assert structure()['preserved_review_meanings'] == 11
