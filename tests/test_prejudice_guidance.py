from scripts import check_prejudice_guidance as checks


def test_same_prejudice_is_used_without_review_for_the_same_persons_judgment():
    assert checks.guidance_checks()['native_same_person_adoption_reason_use_and_no_application_review']


def test_plural_new_opinions_retain_the_old_function_in_the_same_mass():
    assert checks.collective_checks()['plural_real_use_and_same_mass_scope']


def test_old_judgments_and_definitions_remain_unchanged():
    assert checks.structure_checks()['old_definitions_unchanged']
