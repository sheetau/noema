from scripts.check_designation_order import legacy_checks, binding_checks, joint_checks, legacy_scope_checks, structure


def test_legacy_test_masked_argument_order_defect():
    assert legacy_checks()['regression_reproduced']


def test_both_kinds_of_designation_use_one_literal_argument_order():
    assert binding_checks()['same_author_use_order']


def test_corrected_honorific_stays_connected_to_the_full_footnote():
    assert joint_checks()['legacy_du_absent_from_joint_selection']


def test_only_unreviewed_honorific_statement_changes():
    assert structure()['changed_dependency_statement_indices'] == [26]


def test_other_active_legacy_use_already_follows_its_literal_contract():
    assert legacy_scope_checks()['remaining_use_has_literal_node_author_order']
