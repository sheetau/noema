from scripts import check_religious_emphasis_sentence as check


def test_every_ruler_and_same_references():check.content_checks()
def test_retrospective_and_both_reasons_are_retained():check.conjunction_checks()
def test_explanation_preserves_the_existing_departure():check.expansion_checks()
def test_reasons_explanation_anaphora_and_parallel_presentation():check.discourse_checks()
def test_source_reading_previous_reviews_and_roundtrips():check.structure_checks()
