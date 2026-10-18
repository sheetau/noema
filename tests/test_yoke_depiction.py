from scripts.check_yoke_depiction import physical_checks,release_checks,attribution_checks,source_checks,structure


def test_traction_frame_components_share_the_same_part_bearer_and_load():
    assert physical_checks()['required_component_combinations']==16


def test_self_removal_is_more_than_a_missing_or_reclassified_object():
    assert len(release_checks()['contrasts'])==17


def test_literal_world_is_not_executed_by_the_source_depiction_assertion():
    assert attribution_checks()['all_world_primitives_unknown_without_execution']


def test_source_phrase_and_original_image_are_pinned():
    assert source_checks()['range']==[254,315]


def test_existing_manuscript_and_review_bindings_survive():
    assert structure()['total_statements']==34
