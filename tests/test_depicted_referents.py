from scripts import check_depicted_referents as checks


def test_both_referent_ranges_and_edge_endpoints():
    assert checks.range_checks()['two_sided_coverage_and_edge_endpoints_checked']


def test_person_scope_and_cross_person_edges():
    assert checks.person_checks()['no_cross_person_borrowing']


def test_source_binding_without_executing_kind_descriptions():
    assert checks.binding_checks()['kind_description_not_executed']


def test_native_removal_uses_the_same_depicted_targets():
    assert checks.native_checks()['native_removal_and_same_selected_objects_executed']


def test_both_fourth_sentence_parts_require_the_reference():
    assert checks.presentation_checks()['both_attributions_require_same_reference']


def test_prior_judgments_and_reversible_notations_preserved():
    assert checks.structure_checks()['roundtrips']
