from scripts import check_revolution_presentation as checks


def test_extracted_possibility_and_denial_preserve_the_original_claim():
    assert checks.modality_checks()['extracted_conjunction_matches_original']


def test_both_parts_keep_every_public_and_the_same_scope():
    assert checks.scope_checks()['same_nonempty_public_scope_and_all_members']


def test_integrated_presentation_preserves_the_distinct_modal_scopes():
    assert checks.attribution_checks()['uncertainty_denial_and_replacement_have_distinct_scopes']


def test_existing_judgments_and_definitions_are_unchanged():
    assert checks.structure_checks()['old_definitions_unchanged']
