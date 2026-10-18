from scripts.check_periodical_profile import numeral_checks, description_checks, binding_checks, joint_checks, structure


def test_cadence_accepts_positive_integer_numerals_only():
    assert numeral_checks()['numeral_pairs'] == 100


def test_descriptive_use_nominal_policy_and_actual_publication_are_separate():
    assert description_checks()['conventional_cadence_distinct_from_actual_issuance']


def test_same_average_does_not_erase_cycle_and_binding_differences():
    assert binding_checks()['equal_average_frequency_not_same_cycle']


def test_current_title_footnote_and_periodical_description_work_together():
    assert joint_checks()['twelve_assertions_share_existing_references']


def test_previous_text_meanings_and_identifiers_are_preserved():
    assert structure()['preserved_review_selections'] == 10
