from scripts.check_incidental_agreement import modal_checks, intention_checks, argument_checks, source_checks, joint_checks, structure


def test_contingency_requires_a_true_outcome_and_a_distinct_admissible_failure():
    assert modal_checks()['combinations'] == 16


def test_intentions_bind_the_same_process_activity_and_described_result():
    assert intention_checks()['goal_content_not_executed']


def test_source_question_distinguishes_chance_design_necessity_and_unknowns():
    assert source_checks()['opaque_chance_removed_from_active_question']


def test_footnote_can_present_the_question_without_knowing_its_answer():
    assert joint_checks()['connected_assertions'] == 12


def test_revision_preserves_the_ten_existing_whole_unit_readings():
    assert structure()['preserved_review_meanings'] == 10


def test_outcome_adapter_checks_length_order_and_extent_with_ordinary_evaluation():
    assert argument_checks()['no_truncation_or_reordering']
