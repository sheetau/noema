from scripts import check_fourth_paragraph as checks


def test_fifth_sentence_has_contiguous_readings_bound_to_live_definitions():
    assert checks.source_checks()['all_named_definitions_reachable']


def test_all_five_sentences_cover_the_whole_paragraph_without_double_counting():
    assert checks.paragraph_checks()['all_nonblank_positions_covered']


def test_all_prior_judgments_and_integration_evidence_remain_valid():
    assert checks.preservation_checks()['no_language_changes_for_review']
