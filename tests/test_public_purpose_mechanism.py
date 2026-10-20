from scripts.check_public_purpose_mechanism import (
    target_checks, means_checks, purpose_checks, discourse_checks, structure_checks)


def test_shared_goals_and_instrumental_alternatives():
    target_checks()


def test_same_members_and_roles_in_the_means():
    means_checks()


def test_nonfactive_purpose_and_public_goal():
    purpose_checks()


def test_explanatory_transition_and_minimum_alternative():
    discourse_checks()


def test_sentence_record_and_preserved_judgments():
    structure_checks()
